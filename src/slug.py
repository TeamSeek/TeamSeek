import os
import time
import json
import cherrypy
import pystache
from src.cache import PageCache


"""
slug.py

Resolve all non mapped url targets

(essentially just "/" or "/<username>/")
"""

GITHUB_URL='https://github.com/login/oauth/authorize/?client_id={clientID}&redirect_uri={callbackURL}'

cache = PageCache()
with open('.githubAuth', 'r') as f:
    githubAuth = json.load(f)

def createPage(session, params):
    # Render /create page
    initial_data = {'user':session.get('user')}
    return cache.get('layout').render({
        'page_body':cache.getRaw('create'),
        'account_url': '/api/auth/logout',
        'account_action': 'Log Out',
        'initial_data':json.dumps(initial_data)
    })


pages = {
    "create": createPage
}

def render(path, params, session):
    active_user = session.get('user') if 'user' in session else ''
    template = {
        'page_body':'',
        'account_url': '/api/auth/logout',
        'account_action': 'Log Out',
        'active_user':active_user,
        'initial_data':'{}'
    }
    if len(path) == 0:
        # url format '/'
        if 'user' not in session:
            # User is not authenticated
            welcome = cache.get('welcome').render(
                {'client_id':githubAuth["clientID"], 'callbackURL':githubAuth["callbackURL"]})
            template['page_body'] = welcome
            template['account_url'] = GITHUB_URL.format(**githubAuth)
            template['account_action'] = 'Log In'
            return cache.get('layout').render(template)
        else:
            # User is authenticated
            initial_data = {'user':session.get('user')}
            template['initial_data'] = json.dumps(initial_data)
            template['page_body'] = cache.getRaw('dashboard')
            return cache.get('layout').render(template)
    elif len(path) == 1:
        # url format '/pagename'
        if path[0] in pages:
            return pages[path[0]](session, params)
        initial_data = {"user":path[0], "isOwnProfile":path[0]==session.get('user')}
        template['page_body'] = cache.getRaw('user')
        template['initial_data'] = json.dumps(initial_data)
        return cache.get('layout').render(template)
    elif len(path) == 2:
        # url format '/username/projectname'
        isOwnProject = path[0] == session.get('user')
        initial_data = {"user":path[0], "title":path[1], "isOwnProject":isOwnProject}
        template['page_body'] = cache.getRaw('project')
        template['initial_data'] = json.dumps(initial_data)
        return cache.get('layout').render(template)
    else:
        # there are currently no targets with more than two components
        raise cherrypy.HTTPError("404 Not Found")
