#
# this code uses the mosquitto libs to integrate ESP32 sensors via MQTT
# it is experimental but the intention is to make this the default
# sensor mechanism to address the bluetooth integration issues
#
#

import paho.mqtt.client as mqtt
#from time import sleep
import time

# bind to mqtt and listen for landing or outside temperature
# mosquitto_sub -h localhost -t "blehub/sensor/landing_temperature/state"

# This is the Subscriber
insideTag = "blehubn/sensor/landing_temperature/state"
outsideTag = "blehubn/sensor/outside_temperature/state"
hallTag = "blehubn/sensor/hall_temperature/state"
hallTag0 = "blehub/sensor/hall_temperature/state"

tags = { "blehubn/sensor/landing_temperature/state": {
	    "name": 'Landing tag', "time": 0, "temp": 0, "min": 0, "max": 0},
	"blehubn/sensor/outside_temperature/state": {
	    "name": 'Outside tag', "time": 0, "temp": 0, "min": 0, "max": 0},
	"blehubn/sensor/hall_temperature/state": {
	    "name": 'Hall tag', "time": 0, "temp": 0, "min": 0, "max": 0},
	"blehub/sensor/hall_temperature/state": {
	    "name": 'Hall tag0', "time": 0, "temp": 0, "min": 0, "max": 0}}


mtime = time.time() # get the seconds and not a structure
for tag in tags:
   print ("Settting defaults for: ", tags[tag]['name'])
   tags[tag]['time'] = mtime
   tags[tag]['temp'] = 0.0
   tags[tag]['min'] = 100.0
   tags[tag]['max'] = 0.0

if (insideTag in tags):
    print (tags[insideTag])


#tags = {}
#tags[insideTag] = {}
#tags[insideTag]['temp'] = 0.0
#tags[insideTag]['time'] = mtime
#tags[outsideTag] = {}
#tags[outsideTag]['temp'] = 0.0
#tags[outsideTag]['time'] = mtime
#tags[hallTag] = {}
#tags[hallTag]['temp'] = 0.0
#tags[hallTag]['time'] = mtime
#tags[hallTag0] = {}
#tags[hallTag0]['temp'] = 0.0
#tags[hallTag0]['time'] = mtime

#logging.basicConfig(level=logging.INFO)

# 
def secstotime(seconds): 
    min, sec = divmod(seconds, 60) 
    hour, min = divmod(min, 60) 
    return "%d:%02d:%02d" % (hour, min, sec) 

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    #sub = client.subscribe([("blehub/sensor/landing_temperature/state",1),
    #          ("blehub/sensor/outside_temperature/state",2)])
    #client.subscribe("blehub/sensor/outside_temperature/state")
    sub = client.subscribe("+/sensor/+/state")
    #sub = client.subscribe("+/sensor/#")
    #sub = client.subscribe("blehub+/sensor/#")
    #sub = client.subscribe("blehubs/sensor/#")
    #sub = client.subscribe("blehubs/sensor/#")
    print ("sub: ", sub)

def on_message(client, userdata, msg):
    #print (msg.payload, msg.topic)
    #print (msg.payload.decode())
    #print("message received  ", str(msg.payload.decode("utf-8")),
    #                    "topic", msg.topic, "retained ", msg.retain)
    # store the message
    #if msg.payload.decode() == "Hello world!":
    #print("Yes!")
    #client.disconnect()

    # note time as no timestamp and format for printing
    mtime = time.time()
    ctime = time.strftime("%H:%M:%S", time.localtime(mtime))
    #ctime = time.ctime(mtime) # time.strftime("%H:%M:%S", time.localtime(mtime))

    if (msg.topic in tags):
        # what's the difference
        dtime = mtime - tags[msg.topic]['time']
        dstime = secstotime(dtime)
        # and the temp
        temp = msg.payload.decode()

        # note the temp, time and max
        tags[msg.topic]['temp'] = temp
        tags[msg.topic]['time'] = mtime
        if (dtime > tags[msg.topic]['max']):
            tags[msg.topic]['max'] = dtime

        print (tags[msg.topic]['name'], temp, ctime, dstime, tags[msg.topic]['max'])

        #dstime, tags[msg.topic]['max'])

    #print ("processed message")
    """
    if (msg.topic == "blehubn/sensor/landing_temperature/state"):
        #dtime = mtime - tags[msg.topic]['time']
        print ("Landing temp: ", msg.payload.decode(), ctime, dstime, dtime)
    elif (msg.topic == "blehubn/sensor/outside_temperature/state"):
        #dtime = mtime - tags[msg.topic]['time']
        print ("Outside temp: ", msg.payload.decode(), ctime, dstime, dtime)
    elif (msg.topic == "blehubn/sensor/hall_temperature/state"):
        #dtime = mtime - tags[msg.topic]['time']
        print ("Hall temp: ", msg.payload.decode(), ctime, dstime, dtime)
    elif (msg.topic == "blehub/sensor/hall_temperature/state"):
        #dtime = mtime - tags[msg.topic]['time']
        print ("Hall temp 0: ", msg.payload.decode(), ctime, dstime, dtime)
    #else:
        #print ("Unknow mesg: ", msg.payload, msg.topic)
    """
    #tags[msg.topic]['temp'] = msg.payload.decode()
    #tags[msg.topic]['time'] = mtime
    #print (tags)
    
client = mqtt.Client()
#client.username_pw_set(username=”vauto”,password=”ble2020!”)
client.connect("localhost", 1883, 60)

client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()
"""
client.loop_start()
time.sleep(30)
client.loop_stop()
client.disconnect()
"""

# end of file
