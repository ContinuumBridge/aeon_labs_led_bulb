#!/usr/bin/env python
# aeon_labs_led_bulb
# Copyright (C) ContinuumBridge Limited, 2016 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
ModuleName = "aeon_labs_led_bulb"
INTERVAL     = 60      # How often to request sensor values

import sys
import time
import os
from cbcommslib import CbAdaptor
from cbconfig import *
from twisted.internet import threads
from twisted.internet import reactor

colours = ["soft_white", "cold_white", "red", "green", "blue"]

class Adaptor(CbAdaptor):
    def __init__(self, argv):
        self.status =           "ok"
        self.state =            "stopped"
        self.connected =        False
        self.apps =             {"rgbww": []}
        self.colourState = {"soft_white": "0",
            "cold_white": "0",
            "red": "0",
            "green": "0",
            "blue": "0"
        }
        self.switchState =      "0"
        # super's __init__ must be called:
        #super(Adaptor, self).__init__(argv)
        CbAdaptor.__init__(self, argv)
 
    def setState(self, action):
        # error is only ever set from the running state, so set back to running if error is cleared
        if action == "error":
            self.state == "error"
        elif action == "clear_error":
            self.state = "running"
        msg = {"id": self.id,
               "status": "state",
               "state": self.state}
        self.sendManagerMessage(msg)

    def sendCharacteristic(self, characteristic, data, timeStamp):
        msg = {"id": self.id,
               "content": "characteristic",
               "characteristic": characteristic,
               "data": data,
               "timeStamp": timeStamp}
        for a in self.apps[characteristic]:
            reactor.callFromThread(self.sendMessage, msg, a)

    def onStop(self):
        # Mainly caters for situation where adaptor is told to stop while it is starting
        pass

    def pollSensors(self):
        pass

    def onZwaveMessage(self, message):
        self.cbLog("debug", "onZwaveMessage, message: " + str(message))
        if message["content"] == "init":
            self.updateTime = 0
            self.lastUpdateTime = time.time()
        elif message["content"] == "data":
            try:
                self.updateTime = message["data"]["updateTime"]
            except Exception as ex:
                self.cbLog("warning", "onZwaveMessage, unexpected message: " + str(message))
                self.cbLog("warning", "Exception: " + str(type(ex)) + str(ex.args))

    def onOff(self, s):
        if s == "on":
            return "255"
        else:
            return "0"

    def switch(self, value):
        cmd = {"id": self.id,
               "request": "post",
               "address": self.addr,
               "instance": "0",
               "commandClass": "0x33",
               "action": "Set",
               "value": value 
              }
        self.sendZwaveMessage(cmd)

    def onAppInit(self, message):
        self.cbLog("debug", "onAppInit, message: " + str(message))
        resp = {"name": self.name,
                "id": self.id,
                "status": "ok",
                "service": [{"characteristic": "led_rgbww", "interval": 0}],
                "content": "service"}
        self.sendMessage(resp, message["id"])
        self.setState("running")

    def onAppRequest(self, message):
        # Switch off anything that already exists for this app
        for a in self.apps:
            if message["id"] in self.apps[a]:
                self.apps[a].remove(message["id"])
        # Now update details based on the message
        for f in message["service"]:
            if message["id"] not in self.apps[f["characteristic"]]:
                self.apps[f["characteristic"]].append(message["id"])
        self.cbLog("debug", "apps: " + str(self.apps))

    def onAppCommand(self, message):
        #self.cbLog("debug", "onAppCommand, req: " +  str(message))
        if "data" not in message:
            self.cbLog("warning", "app message without data: " + str(message))
        else:
            for c in message["data"]:
                if self.colourState[c] != message["data"][c]:
                    self.colourState[c] = message["data"][c]
                    value = str(colours.index(c)) + "," + message["data"][c]
                    self.cbLog("debug", "onAppCommand, value: {}".format(value))
                    self.switch(value)

    def onConfigureMessage(self, config):
        """Config is based on what apps are to be connected.
            May be called again if there is a new configuration, which
            could be because a new app has been added.
        """
        self.setState("starting")

if __name__ == '__main__':
    Adaptor(sys.argv)
