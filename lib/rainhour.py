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

Rainhour 

Implements
==========

- Rainhour

@author: domos  (domos dt vesta at gmail dt com)
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
import json
from datetime import datetime

METEOFRANCEAPIURL = "http://www.meteofrance.com/mf3-rpc-portlet/rest/pluie/"

class RainhourException(Exception):
    """
    Rainhour exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Rainhour:
    """ Rainhour
    """

    def __init__(self, log, send, stop, device_id, weather_id, weather_loc):
        """ Init Rainhour object
            @param log : log instance
            @param send : send
            @param stop : stop flag
            @param device_id : domogik device id
            @param weather_id : Weather location ID
        """
        self.log = log
        self._send = send
        self._stop = stop
        self._device_id = device_id
        self._weather_id = weather_id
        self._weather_loc = weather_loc
 


    def check(self):
        """ Read rain hour forecast
        """
        while not self._stop.isSet():

            the_url = METEOFRANCEAPIURL + self._weather_id
            self.log.debug(u"==> URL API called for the location '%s': '%s'" % (self._weather_loc, the_url))
            try:
                req = urllib2.urlopen(the_url)
                jsondata = json.loads(req.read().decode('ascii', errors='ignore'))            # Probleme with unicode !
                #self.log.info(u"==== '%s'" % format(jsondata))
            except HTTPError, err:
                self.log.error(u"### API GET '%s', HTTPError code: %d" % (the_url, err.code) )
            except URLError, err:
                self.log.error(u"### API GET '%s', URLError reason: %s" % (the_url, err.reason) )
            except ValueError:
                self.log.error(u"### API GET '%s', no json data" % the_url)
            else:
                if jsondata["isAvailable"] and jsondata["hasData"]:
                    self.log.info(u"==> Location '%s' echeance = '%s'" % (self._weather_loc, jsondata["echeance"]))
                    rainForecastDate = datetime.strptime(jsondata["echeance"], "%Y%m%d%H%M").strftime("%Y-%m-%dT%H:%M")     
                    
                    rainForecastTxt = jsondata["niveauPluieText"]
                    self.log.info(u"==> Location '%s' rainForecastTxt = '%s'" % (self._weather_loc, format(rainForecastTxt)))
                    rainForecastNb = self.rainForecastTxt2Nb(rainForecastTxt)
                    self.log.info(u"==> Location '%s' rainForecastNb = '%s'" % (self._weather_loc, format(rainForecastNb)))
                    
                    rainInHour = 0
                    heavyRainInHour = 0
                    rainHourForecast = {}
                    minutesdelta = 0
                    for rainlevel in jsondata["dataCadran"]:
                        if rainlevel["niveauPluie"] > 1 : rainInHour = 1
                        if rainlevel["niveauPluie"] == 4 : heavyRainInHour = 1
                        rainHourForecast[minutesdelta] = rainlevel["niveauPluie"]
                        minutesdelta += 5

                    #self.log.debug(u"==> Rain forecast for the location '%s': rainForecastDate='%s', rainInHour=%d, heavyRainInHour=%d, rainHourForecast: %s" % (self._weather_loc, rainForecastDate, rainInHour, heavyRainInHour, format(rainHourForecast)))
                    self._send(self._device_id, rainForecastDate, rainInHour, heavyRainInHour, rainHourForecast, rainForecastNb, self._weather_loc)
                else:
                    self.log.warning(u"### No rain data available for this location '%s': %s" % (self._weather_loc, format(jsondata)))
            self._stop.wait(300)


    def rainForecastTxt2Nb(self, listtxt):
        dict = { "De": "", "Pas de prcipitations": "1", "Prcipitations faibles": "2", "Prcipitations modres": "3", "Prcipitations fortes": "4", " : ": ":", "  ": "-"}
        rainForecastNb = ""
        for niveauPluieText in listtxt:
            for i, j in dict.iteritems():
                niveauPluieText = niveauPluieText.replace(i, j)
            rainForecastNb = rainForecastNb + niveauPluieText + ','
            #rainForecastNb.append(niveauPluieText.encode('ascii'))
        return rainForecastNb[0:-1]
        #return "16h35-16h55:1,16h55-17h15:2,17h15-17h35:1"
        #return "22h20-22h25:1,22h30-22h35:2,22h40-22h50:3,22h55-23h00:4,23h05-23h10:5"


