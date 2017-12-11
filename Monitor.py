#!/usr/bin/env python

import os
import datetime
import glob
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time
from constants import MQTTBrokerIP
from constants import MQTTBrokerPort


# global variables
temprobdir = '/sys/bus/w1/devices/28*'
devicelist = glob.glob(temprobdir)                              # Get list of 1-wire devices

# GPIO Settings
GPIO.setwarnings(False)                                         # Set warnings to false
GPIO.setmode(GPIO.BCM)                                          # Set GPIO Numbering to match Pinnout
GPIO.setup(17, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)           # Set GPIO Pin 17 - Input (Heating On)
GPIO.setup(18, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)           # Set GPIO Pin 18 - Input (Hotwater On)
GPIO.setup(22, GPIO.OUT)                                        # Set GPIO Pin 22 - Output (Heating On)
GPIO.setup(23, GPIO.OUT)                                        # Set GPIO Pin 23 - Output (Hotwater On)

# Connect to MQTT Broker
mqttclient = mqtt.Client()
mqttclient.connect(MQTTBrokerIP, MQTTBrokerPort)
mqttclient.loop_start()


def on_connect(client, userdata, rc):
    # Do something when connected to MQTT Broker
    print('info', 'monitor.py', 'Connected to MQTT Broker')


def on_disconnect(client, userdata, rc):
    # Do something when connected to MQTT Broker
    print('info', 'monitor.py', 'Disconnected from MQTT Broker')


def SendMQTT_TempUpdate(deviceid, temp):
    # Send the temperature to the MQTT Broker
    mqttclient.publish("ourHome/temperatures/" + deviceid, temp)


def SendMQTT_StatusUpdate(GPIOport):
    # Send the status of a GPIO port to the MQTT Broker
    status = str(GPIO.input(GPIOport))
    mqttclient.publish("ourHome/boiler/" + str(GPIOport), status)
    GPIO.output(GPIOport+5, status)

# get temperature from device
def get_temperature(devicefile):
    try:
        fileobj = open(devicefile, 'r')
        lines = fileobj.readlines()
        fileobj.close()
    except:
        return None

    # get the status from line 1
    status = lines[0][-4:-1]

    # get the temperature from line 2
    if status == "YES":
        tempstr = lines[1].split()[-1]
        tempvalue = float(tempstr[2:])/1000
        return "%.2f" % tempvalue
    else:
        return None


# Main Function
GPIO.add_event_detect(17, GPIO.RISING, callback=SendMQTT_StatusUpdate, bouncetime=300) 
GPIO.add_event_detect(18, GPIO.RISING, callback=SendMQTT_StatusUpdate, bouncetime=300) 

while True:
    starttime = time.time()
    if devicelist != '[]':
        for id in devicelist:
            # Get temperature from the each device connected
            temperature = get_temperature(id + '/w1_slave')
            if temperature != None:
                SendMQTT_TempUpdate(id[-15:], temperature)
            else:
                temperature = get_temperature(id + '/w1_slave')
                SendMQTT_TempUpdate(id[-15:], temperature)
	
    time.sleep(30.0 - ((time.time() - starttime) % 30.0)))
			
mqttclient.disconnect()
