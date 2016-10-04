#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

RainHour

Implements
==========

- RainhourManager

@author: domos  (domos dt vesta at gmail dt com)
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.plugin import Plugin
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq

from domogik_packages.plugin_rainhour.lib.rainhour import Rainhour, RainhourException
import threading
import traceback
import re
import json
import time

class RainhourManager(Plugin):
    """ Get rainhourrmation informations
    """

    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='rainhour')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        #if not self.check_configured():
        #    return

        # get the devices list
        self.devices = self.get_device_list(quit_if_no_device = True)
        #self.log.info(u"==> device:   %s" % format(self.devices))

        # get the sensors id per device : 
        # {device_id1 : {"sensor_name1" : sensor_id1, "sensor_name2" : sensor_id2},  device_id2 : {"sensor_name1" : sensor_id1, "sensor_name2" : sensor_id2}}
        self.sensors = self.get_sensors(self.devices)
        self.log.info(u"==> sensors:   %s" % format(self.sensors))        # INFO ==> sensors:   {66: {u'rainhour': 159}}  ('device id': 'sensor name': 'sensor id')

        # create a Rainhour for each device
        threads = {}
        rainhour_list = {}
        for a_device in self.devices:
            try:
                # global device parameters
                weather_id = self.get_parameter(a_device, "location")
                
                weather_loc = self.get_parameter(a_device, "locationname")[0:-8]       # Delete "postal code".
                device_id = a_device["id"]
                self._pub.send_event('client.sensor', { self.sensors[device_id]["rainForecastLocation"]: weather_loc })  # Store "Location Name" in sensor for use by widget !
                
                rainhour_list[weather_id] = Rainhour(self.log, self.send_data, self.get_stop(), device_id, weather_id)

                # start the rainhour thread
                self.log.info(u"Start to check rainhour forecast '{0}'".format(weather_id))
                thr_name = "{0}".format(weather_id)
                threads[thr_name] = threading.Thread(None,
                                              rainhour_list[weather_id].check,
                                              thr_name,
                                              (),
                                              {})
                threads[thr_name].start()
                self.register_thread(threads[thr_name])

            except:
                self.log.error(u"{0}".format(traceback.format_exc()))
                # we don't quit plugin if an error occured
                # a rainhour device can be KO and the others be ok
                #self.force_leave()
                #return

        self.ready()
        self.log.info(u"Plugin ready :)")




    def send_data(self, device_id, rainForecastDate, rainInHour, heavyRainInHour, rainHourForecast, rainForecastTxt):
        """ Send the rainhour sensors values over MQ
        """
        data = {}
        data[self.sensors[device_id]["rainForecastDate"]] = rainForecastDate     #  "rainForecastDate" = sensor name in info.json file
        data[self.sensors[device_id]["rainInHour"]] = rainInHour                 #  "rainInHour" = sensor name in info.json file
        data[self.sensors[device_id]["heavyRainInHour"]] = heavyRainInHour       #  "heavyRainInHour" = sensor name in info.json file
        data[self.sensors[device_id]["rainForecastTxt"]] = str(rainForecastTxt)  #  "rainForecastNb" = sensor name in info.json file
        
        for minutesdelta in xrange(0, 56, 5):
            data[self.sensors[device_id]["rainLevel" + str(minutesdelta) + "mn"]] = rainHourForecast[minutesdelta]
        
        self.log.info("==> 0MQ PUB sended = %s" % format(data))

        try:
            self._pub.send_event('client.sensor', data)
        except:
            #We ignore the message if some values are not correct because it can happen with rainhour ...
            self.log.debug(u"Bad MQ message to send. This may happen due to some invalid rainhour data. MQ data is : {0}".format(data))
            pass


        
if __name__ == "__main__":
    rainhour = RainhourManager()
