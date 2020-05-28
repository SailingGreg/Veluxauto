#
#
#
#

# standard imports
import logging
import time

# needed for html requests
import requests
import json
import datetime
from datetime import date
import dateutil.relativedelta
from dateutil import parser
#import pyowm # wraps open weather apis
from lxml import html
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

weewxurl = "http://pihmwstn/daily.json"

def removeNonAscii(s):
    return "".join(i for i in s if (ord(i)<128 and ord(i)>31))


# load the weather date from WeeWx
def loadWeather():

    try:
        req = requests.get(weewxurl)
    except Exception as e:
        print ("Error on request")

    return (req.json)

# end loadWeather



# main

while (True):

    weather = loadWeather()

    print (weather)

    time.sleep (10)

# end while

# end main
