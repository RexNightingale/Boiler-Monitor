#!/usr/bin/env python

import os
import datetime
import glob
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from constants import MQTTBrokerIP
from constants import MQTTBrokerPort


# global variables
temprobdir = '/sys/bus/w1/devices/28*'


# GPIO Settings
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)                                          # Set GPIO Numbering to match Pinnout
GPIO.setup(17, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)           # Set GPIO Pin 17 - Input (Heating On)
GPIO.setup(18, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)           # Set GPIO Pin 18 - Input (Hotwater On)
GPIO.setup(22, GPIO.OUT)                                        # Set GPIO Pin 22 - Output (Heating On)
GPIO.setup(23, GPIO.OUT)                                        # Set GPIO Pin 23 - Output (Hotwater On)


def on_connect(client, userdata, rc):
    # Do something when connected to MQTT Broker
    print('info', 'monitor.py', 'Connected to MQTT Broker')


def on_disconnect(client, userdata, rc):
    # Do something when connected to MQTT Broker
    print('info', 'monitor.py', 'Disconnected from MQTT Broker')


# connect to MQTT Broker
mqttclient = mqtt.Client()
#mqttclient.on_connect = on_connect
#mqttclient.on_disconnect = on_disconnect
mqttclient.connect(MQTTBrokerIP, MQTTBrokerPort)
mqttclient.loop_start()


def log_temp_mqtt(deviceid, temp):
    # Send the temperature to the MQTT Broker
    mqttclient.publish("ourHome/temperatures/" + deviceid, temp)


def log_status_mqtt(deviceid, status):
    # Send the temperature to the MQTT Broker
    mqttclient.publish("ourHome/boiler/" + deviceid, status)


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
def main():
    # Get list of devices
    devicelist = glob.glob(temprobdir)

    if devicelist == '[]':
        return None
    else:
        for id in devicelist:
            # Get temperature from the each device connected
            temperature = get_temperature(id + '/w1_slave')
            if temperature != None:
                log_temp_mqtt(id[-15:], temperature)
            else:
                temperature = get_temperature(id + '/w1_slave')
                log_temp_mqtt(id[-15:], temperature)

    for loop in range(17, 18):
	input = str(GPIO.input(loop))
        log_status_mqtt(str(loop), input)
				
    mqttclient.disconnect()

if __name__=="__main__": main()
