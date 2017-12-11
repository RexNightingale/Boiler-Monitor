#!/usr/bin/env python

import os
import datetime
import glob
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time
from logger import logmessage
from constants import MQTTBrokerIP
from constants import MQTTBrokerPort


# global variables
temprobdir = '/sys/bus/w1/devices/28*'
pollcycle = 30                                                  # set pollcycle time

# GPIO Settings
GPIO.setwarnings(False)                                         # Set warnings to false
GPIO.setmode(GPIO.BCM)                                          # Set GPIO Numbering to match Pinnout
GPIO.setup(17, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)           # Set GPIO Pin 17 - Input (Heating On)
GPIO.setup(18, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)           # Set GPIO Pin 18 - Input (Hotwater On)
GPIO.setup(22, GPIO.OUT)                                        # Set GPIO Pin 22 - Output (Heating On)
GPIO.setup(23, GPIO.OUT)                                        # Set GPIO Pin 23 - Output (Hotwater On)

# Connect to the MQTT Broker
def connectMQTT():
    global mqttclient
    while True:
        mqttclient = mqtt.Client()
        mqttclient.on_connect = on_connect
        mqttclient.on_disconnect = on_disconnect
        try:
            mqttclient.connect(MQTTBrokerIP, MQTTBrokerPort)
            mqttclient.loop_start()
            break
        except:
            logmessage('error', 'monitor.py', 'Error connecting to the MQTT Broker')
            time.sleep(30)


# Do something when connected to MQTT Broker
def on_connect(client, userdata, rc):
    logmessage('info', 'monitor.py', 'Connected to MQTT Broker')


# Do something when connected to MQTT Broker
def on_disconnect(client, userdata, rc):
    logmessage('info', 'monitor.py', 'Disconnected from MQTT Broker')


# Send the temperature to the MQTT Broker
def SendMQTT_TempUpdate(deviceid, temp):
    mqttclient.publish("ourHome/temperatures/" + deviceid, temp)


# Send the status of a GPIO port to the MQTT Broker
def SendMQTT_StatusUpdate(GPIOport):
    status = str(GPIO.input(GPIOport))
    mqttclient.publish("ourHome/boiler/" + str(GPIOport), status)
    # Switch on corresponding status LED
    # GPIO 22 = Heating
    # GPIO 23 = Water
    GPIO.output(GPIOport + 5, status)

# Get temperature from 1-wire device
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


def main():
    # Connect to the MQTT Broker
    connectMQTT()
    
    # Setup GPIO ports for listening to event changes
    GPIO.add_event_detect(17, GPIO.RISING, callback=SendMQTT_StatusUpdate, bouncetime=300) 
    GPIO.add_event_detect(18, GPIO.RISING, callback=SendMQTT_StatusUpdate, bouncetime=300) 
    
    while True:
        starttime = time.time()
        # Get list of 1-wire devices
        devicelist = glob.glob(temprobdir)
        # Read temperature values from 1-wire devices
        if devicelist != '[]':
            for id in devicelist:
                # Get temperature from the each device connected
                temperature = get_temperature(id + '/w1_slave')
                if temperature != None:
                    SendMQTT_TempUpdate(id[-15:], temperature)
                else:
                    temperature = get_temperature(id + '/w1_slave')
                    SendMQTT_TempUpdate(id[-15:], temperature)
        # Read GPIO status indicators
        for loop in range(17, 18):
            SendMQTT_StatusUpdate(loop)
        
        time.sleep(pollcycle - ((time.time() - starttime) % pollcycle)))

if __name__ == '__main__': main()
