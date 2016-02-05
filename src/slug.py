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

cache = PageCache()

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
    if len(path) == 1:
        # format /pagename
        if path[0] in pages:
            return pages[path[0]](session, params)
        initial_data = {"user":path[0], "isOwnProfile":path[0]==session.get('user')}
        return cache.get('layout').render({
            'page_body':cache.getRaw('user'),
            'account_url': '/api/auth/logout',
            'account_action': 'Log Out',
            'initial_data':json.dumps(initial_data)
        })
    elif len(path) == 2:
        # format /username/projectname
        isOwnProject = path[0] == session.get('user')
        initial_data = {"user":path[0], "title":path[1], "isOwnProject":isOwnProject}
        return cache.get('layout').render({
            'page_body':cache.getRaw('project'),
            'account_url': '/api/auth/logout',
            'account_action': 'Log Out',
            'initial_data':json.dumps(initial_data)
        })
    elif len(path) > 2:
        return "Unrecognized url"
    if 'user' not in session:
        # If session info does not exist render the welcome page
        return cache.get('layout').render({
            'page_body':cache.getRaw('welcome'),
            'account_url': '/api/auth/login',
            'account_action': 'Log In'
        })
    else:
        # TODO, make sure the user has a valid session token
        initial_data = {'user':session.get('user')}
        return cache.get('layout').render({
            'page_body':cache.getRaw('dashboard'),
            'account_url': '/api/auth/logout',
            'account_action': 'Log Out',
            'initial_data':json.dumps(initial_data)
        })
