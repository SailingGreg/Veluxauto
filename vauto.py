#
# Velux automation code - controls the main skylight
# based on the temperature difference and time of day
#
#

# standard imports
import logging
import time
import PiRelay

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


# main processing loop

# create and reset the relays
relay1 = PiRelay.Relay("RELAY1")
relay2 = PiRelay.Relay("RELAY2")

# the starting state
windowState = CLOSED
Operating = True

while (True):

    weather = loadWeather()

    #print (weather)

    print (weather['title'], weather['time'])
    # extract the inside and outside temperatures
    toutTemp = weather['stats']['current']['outTemp']
    tinTemp = weather['stats']['current']['insideTemp']

    # convert the encode strings
    inTemp = float(BeautifulSoup(tinTemp, "lxml").text[0:-2])
    outTemp = float(BeautifulSoup(toutTemp, "lxml").text[0:-2])
    print ("inside/outside temp", inTemp, outTemp)

    # if it is later in the day and temperature outside is less than
    # inside temperature open the window

    # check operating window - this sets time constraints

    # add time check and flag if 'operating'
    if (Operating == True \
			and outTemp < 22 \
			and outTemp < (inTemp - 1.5)):
        if (windowState != OPEN):
            print ("Windowing open")
            relay1.on()
            time.sleep(0.5)
            relay1.off()
            windowState = OPEN
    else:
        if (windowState != CLOSED): # it should be
            print ("Closing window")
            relay2.on()
            time.sleep(0.5)
            relay2.off()
            windowState = CLOSED

    #time.sleep (10)
    time.sleep (FIVEMINS)

# end while

# end main
