#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# sms-bridge
#	Sends sms messages
#

#  todo also monitor google voice for sms messages and voice mails
# 	download them and keep an active count of unread
#	publish the count to a topic and provide a way to retreive/play them
#


__author__ = "Dennis Sell"
__copyright__ = "Copyright (C) Dennis Sell"


import sys
import subprocess
import mosquitto
import os, tempfile
import time
import signal

from googlevoice import Voice
from config import Config


CLIENT_NAME = "mqtt2sms"
CLIENT_VERSION = "0.6"
MQTT_TIMEOUT = 60	#seconds


#TODO might want to add a lock file
#TODO  need to deal with no config file existing!!!
#read in configuration file
homedir = os.path.expanduser("~")
f = file(homedir + '/.mqtt2sms.conf')
cfg = Config(f)
MQTT_HOST = cfg.MQTT_HOST
MQTT_PORT = cfg.MQTT_PORT
CLIENT_TOPIC = cfg.CLIENT_TOPIC
BASE_TOPIC = cfg.BASE_TOPIC
#TODO  need to finish using config values


#define what happens after connection
def on_connect( self, obj, rc):
	global mqtt_connected
	mqtt_connected = True
	print "MQTT Connected"
	mqttc.publish ( CLIENT_TOPIC + "status" , "connected", 1, 1 )
	mqttc.publish( CLIENT_TOPIC + "version", CLIENT_VERSION, 1, 1 )
	mqttc.subscribe( CLIENT_TOPIC + "message", 2 )
	mqttc.subscribe( CLIENT_TOPIC + "ping", 2)


def on_disconnect( self, obj, rc ):
	pass


#On recipt of a message process it
def on_message(self, obj, msg):
	global voicec
	if (( msg.topic == CLIENT_TOPIC + "ping" ) and ( msg.payload == "request" )):
		mqttc.publish( CLIENT_TOPIC + "ping", "response", qos = 1, retain = 0 )
	else:
		if (( msg.topic == CLIENT_TOPIC + "message" ) and ( msg.payload != "" )):
			voicec.login()
			sms_msg = msg.payload.split(':')
			print "Sending SMS to: ", sms_msg[0]
			print "Message: ", sms_msg[1]
			voicec.send_sms( sms_msg[0], sms_msg[1] )


def mqtt_connect():
	rc = 1
	while ( rc ):
		print "Attempting connection..."
		mqttc.will_set( CLIENT_TOPIC + "status", "disconnected_", 1, 1)

		#define the mqtt callbacks
		mqttc.on_message = on_message
		mqttc.on_connect = on_connect
		mqttc.on_disconnect = on_disconnect

		#connect
		rc = mqttc.connect( MQTT_HOST, MQTT_PORT, MQTT_TIMEOUT )
		if rc != 0:
			logging.info( "Connection failed with error code $s, Retrying", rc )
			print "Connection failed with error code ", rc, ", Retrying in 30 seconds."
			time.sleep(30)
		else:
			print "Connect initiated OK"


def mqtt_disconnect():
	global mqtt_connected
	if ( mqtt_connected ):
		mqtt_connected = False 
		print "MQTT Disconnected"
	mqttc.disconnect()


def cleanup(signum, frame):
	global running
	running = False
	mqtt_disconnect()
	sys.exit(signum)





def do_disconnect():
       global mqtt_connected
       mqttc.disconnect()
       mqtt_connected = False
       print "MQTT Disconnected"


#create a broker client
mqttc = mosquitto.Mosquitto( CLIENT_NAME )


#define the callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message

voicec = Voice()

#trap kill signals including control-c
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

def main_loop():
	global mqtt_connected
	mqttc.loop(10)
	while True:
		if ( mqtt_connected ):
			rc = mqttc.loop(10)
			if rc != 0:	
				mqtt_disconnect()
	#			print rc
				print "Stalling for 20 seconds to allow broker connection to time out."
				time.sleep(20)
				mqtt_connect()
				mqttc.loop(10)
		pass


mqtt_connect()
main_loop()



