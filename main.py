#!/usr/bin/env python

import pystache
import cherrypy
import json
import os

from src import create
from src import slug
from src import api
from src import db

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
    _cp_config = {
        'tools.staticdir.on' : True,
        'tools.staticdir.dir' : staticDir,
        'tools.sessions.on' : True,
        'tools.sessions.timeout' : 60 * 24
    }

    @cherrypy.expose
    def default(self, *path, **params):
        return slug.render(path, params, cherrypy.session)

    # map /create/ target
    create = create.WebRoutes()

    # mount the targets from api.WebRoutes at /api/
    api = api.WebRoutes(db)


""" Start application """
cherrypy.quickstart(Router())
