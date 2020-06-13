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
# from requests_toolbelt.utils import dump
import json
import datetime
from datetime import date
import dateutil.relativedelta
from dateutil import parser
# import pyowm # wraps open weather apis
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

    sensor.set_temp_offset(-2.5)
    # sensor.set_temp_offset(-3)

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

# the starting state
windowState = CLOSED
blindState = OPEN
Operating = True
inTemp = 20.0 # starting point so defined on first loop
highTemp = 22.2 # the temperate at which the skylight should open
lowTemp = 21.8 # the temperate at which the skylight should close

while (True):

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

    # convert the encode strings
    # inTemp = float(BeautifulSoup(tinTemp, "lxml").text[0:-2])
    outTemp = float(BeautifulSoup(toutTemp, "lxml").text[0:-2])
    # logging.info ("inside/outside temp: ", str(inTemp), str(outTemp))
    tempStr = "inside/outside temp: " + str(inTemp) + " " + str(outTemp)
    logging.info(tempStr)

    # if it is later in the day and temperature outside is less than
    # inside temperature open the window

    # check operating window - this sets time constraints

    # add time check and flag if 'operating'
    # we need the outside temperature to be pleasant and for it
    # to be a degree or two lower that the inside temperature
    # and for the inside temperature not to drop below 22
    #
    # - add some hysteresis so it doesn't go up and down! - add timer
    if (Operating is True
                          and outTemp <= 22
                          and outTemp < (inTemp - 1.5)
                          and inTemp >= highTemp):
        if (windowState != OPEN):
            logging.info("Windowing opening")
            logger.log(str(weather['time']) + " " +
                                            tempStr + " Windowing opening")
            relay1.on()
            time.sleep(0.5)
            relay1.off()
            windowState = OPEN
    else:
        if (windowState != CLOSED and (inTemp <= lowTemp or outTemp > 22)):
            logging.info("Window closing")
            logger.log(str(weather['time']) + " " +
                                            tempStr + " Windowing closing")
            relay2.on()
            time.sleep(0.5)
            relay2.off()
            #closedTime = time()
            windowState = CLOSED

    # if it is getting too warm outside close the blind
    if (Operating is True and outTemp > highTemp):
       if (blindState != CLOSED):
            logging.info("Blind closing")
            logger.log(str(weather['time']) + " " +
                                            tempStr + " Blind closing")
            relay4.on()
            time.sleep(0.5)
            relay4.off()
            blindState = CLOSED
    else:
        if (blindState == CLOSED and (outTemp < lowTemp)):
            logging.info("Blind opening")
            logger.log(str(weather['time']) + " " +
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
