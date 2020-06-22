#
# Velux automation code - controls the main skylight
# based on the temperature difference and time of day
#
# note the oeld structure is based on the waveshare code
# and therefore the drivers are installed local
#

# standard imports
import logging
import time
import PiRelay
import bme680 # for the environment sensor
from slack_webhook import Slack

from pysolar.solar import *
import pytz
#import datetime

from creds import *

# needed for html requests
import requests
# following only needed for debug, for example iffy json!
# from requests_toolbelt.utils import dump
import json
import datetime
from datetime import date
import dateutil.relativedelta
from dateutil import parser
# import pyowm # wraps open weather apis
from lxml import html
from bs4 import BeautifulSoup

# location
lat = 51.464
log = -0.231

loc = "/home/pi/Veluxauto/" # absolute path for the source directory
# import the SPI & SSD1305 drivers
import sys
sys.path.append(loc + 'drive')
#sys.path.append('./drive')
import SPI
import SSD1305

# and the draw modules
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 24
SPI_PORT = 0
SPI_DEVICE = 0

# 128x32 display with hardware SPI:
disp = SSD1305.SSD1305_128_32(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

FIVEMINS = 300 # 5 mins
TRUE = 1
FALSE = 0
OPEN = True
CLOSED = False

logging.basicConfig(level=logging.INFO)

weewxurl = "http://pihmwstn/daily.json"

def removeNonAscii(s):
    return "".join(i for i in s if (ord(i)<128 and ord(i)>31))

# load the weather data from WeeWx - provides temperatures
oldreq = []
def loadWeather():
    global oldreq

    try:
        req = requests.get(weewxurl)
        oldreq = req # save state
    except Exception as e:
        print("Error on request")
        req = oldreq

    # data = dump.dump_all(req)
    # print(data.decode('utf-8'))

    return (req.json())
# end loadWeather

# def for class
class logAction:

    def __init__(self, loc):
        self.fd = open(loc + 'vauto.actions', 'a+', 1) # line buffering

    def log(self, action):
        self.fd.write(action + "\n")

# end logAction class


def initSensor():
    sensor = bme680.BME680() # sensor object

    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)

    # this is the VOC bit
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    # offset of the order of 3 seems realistic
    # can only do this by observation and comparing
    #sensor.set_temp_offset(-2.5)
    #sensor.set_temp_offset(-3.0)
    sensor.set_temp_offset(-3.2)

    return sensor
# end initSensor

#
# main processing loop
#


# create and reset the relays
relay1 = PiRelay.Relay("RELAY1")
relay2 = PiRelay.Relay("RELAY2")
relay3 = PiRelay.Relay("RELAY3")
relay4 = PiRelay.Relay("RELAY4")

sensor = initSensor() # env sensor
logger = logAction(loc) # local logger
# note: slackHook imported from creds.py
slack = Slack(url = slackHook)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
#width = 128
height = disp.height
#height = 32
image = Image.new('1', (width, height))
# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# load the font file & different sizes
lfont = ImageFont.truetype(loc + '04B_08__.TTF',10)
font = ImageFont.truetype(loc + '04B_08__.TTF',8)
sfont = ImageFont.truetype(loc + '04B_08__.TTF',6)


# the starting state
windowState = CLOSED
blindState = OPEN
Operating = True
inTemp = 20.0 # starting point so defined on first loop
highTemp = 22.2 # the temperate at which the skylight should open
lowTemp = 21.8 # the temperate at which the skylight should close

while (True):

    # get a tz version of now()
    d = datetime.datetime.now()
    #print (d.tzinfo)
    timezone = pytz.timezone("Europe/London")
    date = timezone.localize(d)

    # get the sun's position

    alt_degree = get_altitude(lat, log, date)
    azi_degree = get_azimuth(lat, log, date)
    rad_amnt = radiation.get_radiation_direct(date, alt_degree)

    weather = loadWeather()

    # print(weather)

    time.sleep(2)
    if sensor.get_sensor_data():
        inTemp = sensor.data.temperature
        # sensor.data.temperature, sensor.data.pressure, sensor.data.humidity

    logging.info(str(weather['title']) + " " + str(weather['time']))
    # logging.info(str(weather['title']), str(weather['time']))
    # extract the inside and outside temperatures
    toutTemp = weather['stats']['current']['outTemp']
    tinTemp = weather['stats']['current']['insideTemp']

    # extract sunrise/sunset - note strings so need to convert to time
    sunrise = weather['almanac']['sun']['sunrise']
    sunset = weather['almanac']['sun']['sunset']

    # convert the encode strings
    # inTemp = float(BeautifulSoup(tinTemp, "lxml").text[0:-2])
    outTemp = float(BeautifulSoup(toutTemp, "lxml").text[0:-2])
    # logging.info ("inside/outside temp: ", str(inTemp), str(outTemp))
    #tempStr = "inside/outside temp: " + str(inTemp) + " " + str(outTemp)
    tempStr = "inside/outside temp: {}, {} - {:6.2f} {:6.2f} {:6.2f}".format(inTemp, 
				outTemp, alt_degree, azi_degree, rad_amnt)

    logging.info(tempStr)

    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    top = 0 # row
    x = 0 # column
    # Write two lines of text.
    draw.text((x, top),     "Temperatures: ", font=font, fill=255)
    draw.text((x, top+8),   "Inside: " + str(inTemp), font=font, fill=255)
    draw.text((x, top+16),  "Outside: " + str(outTemp),  font=font, fill=255)
    #draw.text((x, top+25), str(Disk),  font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.display()
    #time.sleep(.1)

    # if it is later in the day and temperature outside is less than
    # inside temperature open the window

    # check operating window - this sets time constraints

    # add time check and flag if 'operating'
    # we need the outside temperature to be pleasant and for it
    # to be a degree or two lower that the inside temperature
    # and for the inside temperature not to drop below 22
    #
    # - add some hysteresis so it doesn't go up and down! - add timer
    if (Operating is True and outTemp <= 22
                          and outTemp < (inTemp - 1.5)
                          and inTemp >= highTemp):
        if (windowState != OPEN):
            logging.info("Windowing opening")
            logger.log(str(weather['time']) + " " +
                                            tempStr + " Windowing opening")
            slack.post(text = str(weather['time']) + " " +
                                            tempStr + " Windowing opening")
            relay1.on()
            time.sleep(0.5)
            relay1.off()
            windowState = OPEN
    else:
        if (windowState != CLOSED and (inTemp <= lowTemp or outTemp > 22.5)):
            logging.info("Window closing")
            logger.log(str(weather['time']) + " " +
                                            tempStr + " Windowing closing")
            slack.post(text = str(weather['time']) + " " +
                                            tempStr + " Windowing closing")
            relay2.on()
            time.sleep(0.5)
            relay2.off()
            #closedTime = time()
            windowState = CLOSED

    blindOffset = 3.5
    # if it is getting too warm outside close the blind
    if (Operating is True and outTemp > highTemp + blindOffset):
       if (blindState != CLOSED):
            logging.info("Blind closing")
            logger.log(str(weather['time']) + " " +
                                            tempStr + " Blind closing")
            slack.post(text = str(weather['time']) + " " +
                                            tempStr + " Blind closing")
            relay4.on()
            time.sleep(0.5)
            relay4.off()
            blindState = CLOSED
    else:
        if (blindState == CLOSED and (outTemp < lowTemp + blindOffset)):
            logging.info("Blind opening")
            logger.log(str(weather['time']) + " " +
                                            tempStr + " Blind opening")
            slack.post(text = str(weather['time']) + " " +
                                            tempStr + " Blind opening")
            relay3.on()
            time.sleep(0.5)
            relay3.off()
            blindState = OPEN

    #time.sleep(10)
    # we wait 5 mins as this is the update freq for weewx
    time.sleep(FIVEMINS)

# end while

# end main
