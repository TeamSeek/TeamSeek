import cherrypy
import json
import requests
import urlparse
import os

from src import users

ALLOW_DEBUG_LOGIN = 'DEBUG_LOGIN' in os.environ

with open('.githubAuth', 'r') as f:
    data = json.load(f)

class WebRoutes(object):
    def __init__(self, db):
        self.db = db
    @cherrypy.expose
    def github(self, **params):
        payload = {'client_id' : data["clientID"], 'client_secret' : data["client_secret"], 'code' : params['code']}
        # Use code to get access token
        result = requests.post('https://github.com/login/oauth/access_token', data=payload)
        parsedata = urlparse.parse_qs(result.text)
        # Store access token in session
        cherrypy.session['githubToken'] = parsedata["access_token"][0]
        headers = {'content-type': 'application/json', 'Authorization':'token {0}'.format(cherrypy.session.get('githubToken'))}
        # Use access token to get user info
        result = requests.get('https://api.github.com/user', headers=headers).json()
        # Create user if does not already exist
        cursor = self.db.connection.cursor()
        users.add_new_user(cur=cursor, username=result['login'], email=result['email'])
        # Store username in session
        cherrypy.session['user'] = result["login"]
        raise cherrypy.HTTPRedirect("/")
    @cherrypy.expose
    def logout(self, **params):
        cherrypy.session.delete()
        raise cherrypy.HTTPRedirect("/")
    @cherrypy.expose
    def debug(self, **params):
        if not ALLOW_DEBUG_LOGIN:
            return json.dumps({'error':'debug auth not supported'})
        if 'user' not in params:
            return json.dumps({'error':'user not provided in query string'})
        cherrypy.session['user'] = params['user']
        raise cherrypy.HTTPRedirect("/")
    @cherrypy.expose
    def whoami(self, **params):
        if 'user' not in cherrypy.session:
            ret = {'error': 'session not authorized'}
        else:
            ret = {'user':cherrypy.session.get('user')}
        return json.dumps(ret)
