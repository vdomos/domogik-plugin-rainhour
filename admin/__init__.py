# -*- coding: utf-8 -*-

### common imports
from flask import Blueprint, abort
from domogik.common.utils import get_packages_directory
from domogik.admin.application import render_template
from domogik.admin.views.clients import get_client_detail
from jinja2 import TemplateNotFound

### package specific imports
#import os
import traceback
from flask_wtf import Form
from wtforms import TextField, validators
from flask import request

import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError
import json
import subprocess


### package specific functions
def search_location(name):
        the_url = "http://www.meteofrance.com/mf3-rpc-portlet/rest/lieu/facet/pluie/search/" + name
        print(u"===> The value URL Search called: '%s'" % the_url)
        try:
            req = urllib2.urlopen(the_url)
            jsondata = json.loads(req.read().decode('ascii', errors='ignore'))
        except HTTPError, err:
            print(u"#### API GET '%s', HTTPError code: %d" % (the_url, err.code) )
            return []     
        except URLError, err:
            print(u"#### API GET '%s', URLError reason: %s" % (the_url, err.reason) )
            return []     
        except ValueError:
            print(u"#### API GET '%s', no json data" % the_url)
            return []    
        return jsondata


def get_errorlog(cmd, log):
    print("Command = %s" % cmd)
    errorlog = subprocess.Popen([cmd, log], stdout=subprocess.PIPE)
    output = errorlog.communicate()[0]
    if isinstance(output, str):
        output = unicode(output, 'utf-8')
    return output



class LocationForm(Form):
    location = TextField("location")



### common tasks
package = "plugin_rainhour"
template_dir = "{0}/{1}/admin/templates".format(get_packages_directory(), package)
static_dir = "{0}/{1}/admin/static".format(get_packages_directory(), package)
geterrorlogcmd = "{0}/{1}/admin/geterrorlog.sh".format(get_packages_directory(), package)
logfile = "/var/log/domogik/{0}.log".format(package)

plugin_rainhour_adm = Blueprint(package, __name__,
                        template_folder = template_dir,
                        static_folder = static_dir)


@plugin_rainhour_adm.route('/<client_id>', methods = ['GET', 'POST'])
def index(client_id):
    detail = get_client_detail(client_id)
    form = LocationForm()
    if request.method == "POST":
        result = search_location(form.location.data)
    else:
        result = []
    try:
        return render_template('plugin_rainhour.html',
                clientid = client_id,
                client_detail = detail,
                mactive="clients",
                active = 'advanced',
                informations = result,
                errorlog = get_errorlog(geterrorlogcmd, logfile),
                form = form)
    except TemplateNotFound:
        abort(404)
        


