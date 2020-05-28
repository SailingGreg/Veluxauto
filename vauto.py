#
#
#
#

# standard imports
import logging
import time

# needed for html requests
import requests
#import reqdump
from requests_toolbelt.utils import dump
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
        req = requests.get(weewxurl )
    except Exception as e:
        print ("Error on request")

    #data = dump.dump_all(req)
    #print(data.decode('utf-8'))

    #print(req.request.body)
    #print(req.request.headers)

    return (req.json())

# end loadWeather



# main

while (True):

    weather = loadWeather()

    #print (weather)

    print (weather['title'], weather['time'])
    # extract the inside and outside temperatures
    outTemp = weather['stats']['current']['outTemp']
    inTemp = weather['stats']['current']['insideTemp']

    # convert the encode strings
    cinTemp = BeautifulSoup(inTemp, "lxml").text
    coutTemp = BeautifulSoup(outTemp, "lxml").text
    print ("inside temp", float(cinTemp[0:-2]))
    print ("outside temp", float (coutTemp[0:-2]))


    time.sleep (10)

# end while

# end main
