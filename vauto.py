#
# Velux automation code - controls the main skylight
# based on the temperature difference and time of day
#
#

# standard imports
import logging
import time
import PiRelay
import bme680 # for the environment sensor

# needed for html requests
import requests
# following only needed for debug, for example iffy json!
#from requests_toolbelt.utils import dump
import json
import datetime
from datetime import date
import dateutil.relativedelta
from dateutil import parser
#import pyowm # wraps open weather apis
from lxml import html
from bs4 import BeautifulSoup

FIVEMINS = 300 # 5 mins
TRUE = 1
FALSE = 0
OPEN = True
CLOSED = False

logging.basicConfig(level=logging.INFO)

weewxurl = "http://pihmwstn/daily.json"
loc = "/home/pi/Veluxauto/" # absolute path for the source directory

def removeNonAscii(s):
    return "".join(i for i in s if (ord(i)<128 and ord(i)>31))


# load the weather data from WeeWx - provides temperatures
oldreq = 0
def loadWeather():

    try:
        req = requests.get(weewxurl )
        oldreq = req # save state
    except Exception as e:
        print ("Error on request")
        req = oldreq

    #data = dump.dump_all(req)
    #print(data.decode('utf-8'))

    return (req.json())
# end loadWeather

fd = None
def logAction(action):
    global fd

    if (fd is None):
        fd = open(loc + 'vauto.actions', 'a+', 1) # line buffering

    # need to add timestamp
    fd.write(action + "\n")
# end logAction

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

    sensor.set_temp_offset(-2.5)
    #sensor.set_temp_offset(-3)

    return sensor
# end initSensor

#
# main processing loop
#

# create and reset the relays
relay1 = PiRelay.Relay("RELAY1")
relay2 = PiRelay.Relay("RELAY2")

sensor = initSensor()

# the starting state
windowState = CLOSED
Operating = True
inTemp = 20.0 # starting point so defined on first loop

while (True):

    weather = loadWeather()

    #print (weather)

    time.sleep (2)
    if sensor.get_sensor_data():
        inTemp = sensor.data.temperature
        # sensor.data.temperature, sensor.data.pressure, sensor.data.humidity

    logging.info (str(weather['title']) + " " + str(weather['time']))
    #logging.info (str(weather['title']), str(weather['time']))
    # extract the inside and outside temperatures
    toutTemp = weather['stats']['current']['outTemp']
    tinTemp = weather['stats']['current']['insideTemp']

    # convert the encode strings
    #inTemp = float(BeautifulSoup(tinTemp, "lxml").text[0:-2])
    outTemp = float(BeautifulSoup(toutTemp, "lxml").text[0:-2])
    #logging.info ("inside/outside temp: ", str(inTemp), str(outTemp))
    logging.info ("inside/outside temp: " + str(inTemp) + " " + str(outTemp))

    # if it is later in the day and temperature outside is less than
    # inside temperature open the window

    # check operating window - this sets time constraints

    # add time check and flag if 'operating'
    # we need the outside temperature to be pleasant and for it
    # to be a degree or two lower that the inside temperature
    # and for the inside temperature not to drop below 22
    # - add some hysteresis so it doesn't go up and down! - add timer
    if (Operating == True \
			and outTemp <= 22 \
			and outTemp < (inTemp - 1.5) \
			and inTemp >= 22):
        if (windowState != OPEN):
            logging.info ("Windowing opening")
            logAction (str(weather['time']) + " Windowing opening")
            relay1.on()
            time.sleep(0.5)
            relay1.off()
            windowState = OPEN
    else:
        if (windowState != CLOSED): # it should be
            logging.info ("Window closing")
            logAction (str(weather['time']) + " Windowing closing")
            relay2.on()
            time.sleep(0.5)
            relay2.off()
            #closedTime = time()
            windowState = CLOSED

    #time.sleep (10)
    # we wait 5 mins as this is the update freq for weewx
    time.sleep (FIVEMINS)

# end while

# end main
