#!/usr/bin/python

# Library for PiRelay
# Developed by: SB Components
# Author: Ankur
# Project: PiRelay
# Python: 3.4.2

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

class Relay:
    ''' Class to handle Relay

    Arguments:
    relay = string Relay label (i.e. "RELAY1","RELAY2","RELAY3","RELAY4")
    '''
    relaypins = {"RELAY1":31, "RELAY2":33, "RELAY3":35, "RELAY4":37}


    def __init__(self, relay):
        self.pin = self.relaypins[relay]
        self.relay = relay
        GPIO.setup(self.pin,GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        #print(self.relay + " - ON")
        GPIO.output(self.pin,GPIO.HIGH)

    def off(self):
        #print(self.relay + " - OFF")
        GPIO.output(self.pin,GPIO.LOW)
