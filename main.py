#!/usr/bin/env python

import cherrypy
import json
import os

from src import api
from src import db
from src import skills

# Default port number
PORT = 8080


# Overwrite port if env.CHERRYPY_PORT is defined
if 'CHERRYPY_PORT' in os.environ:
    PORT = int(os.environ['CHERRYPY_PORT'])
    cherrypy.config.update({'server.socket_port': PORT})


# Get directory for static files
thisDir = os.path.dirname(os.path.realpath(__file__))
staticDir = os.path.join(thisDir, 'public')

db = db.PostgreSQL()

class Router(object):
    """ Main router object for Teamseek """
    _cp_config = {'tools.staticdir.on' : True,
                  'tools.staticdir.dir' : staticDir,
                  'tools.staticdir.index' : 'index.html'
    }
    # mount the targets from api.WebRoutes at /api/
    api = api.WebRoutes()

    # mount the targets from skills.Fetch at /skills/
    # pass database connection to Fetch() object
    skills = skills.Fetch(db.connection)


""" Start application """
cherrypy.quickstart(Router())
