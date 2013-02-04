#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim tabstop=4 expandtab shiftwidth=4 softtabstop=4

#
# sms-bridge
#    Sends sms messages
#

#  todo also monitor google voice for sms messages and voice mails
#     download them and keep an active count of unread
#    publish the count to a topic and provide a way to retreive/play them
#


__author__ = "Dennis Sell"
__copyright__ = "Copyright (C) Dennis Sell"


APPNAME = "mqtt2sms"
VERSION = "0.8"
WATCHTOPIC = "/raw/" + APPNAME + "/command"

from googlevoice import Voice
from daemon import Daemon
from mqttcore import MQTTClientCore
from mqttcore import main


class MyMQTTClientCore(MQTTClientCore):
    def __init__(self, appname, clienttype):
        MQTTClientCore.__init__(self, appname, clienttype)
        self.clientversion = VERSION
        self.watchtopic = WATCHTOPIC
        self.voicec = Voice()

    def on_connect(self, mself, obj, rc):
        MQTTClientCore.on_connect(self, mself, obj, rc)
        self.mqttc.subscribe(self.watchtopic, qos=2)

    def on_message(self, mself, obj, msg):
        MQTTClientCore.on_message(self, mself, obj, msg)
        if (msg.topic == self.watchtopic):
            if ((msg.topic == self.watchtopic + "/message") and
                    (msg.payload != "")):
                self.voicec.login()
                sms_msg = msg.payload.split(':')
                print "Sending SMS to: ", sms_msg[0]
                print "Message: ", sms_msg[1]
                self.voicec.send_sms(sms_msg[0], sms_msg[1])


class MyDaemon(Daemon):
    def run(self):
        mqttcore = MyMQTTClientCore(APPNAME, clienttype="type1")
        mqttcore.main_loop()


if __name__ == "__main__":
    daemon = MyDaemon('/tmp/' + APPNAME + '.pid')
    main(daemon)
