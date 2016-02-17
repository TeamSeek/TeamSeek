import json
import cherrypy
from src.cache import PageCache

cache = PageCache()
class WebRoutes(object):
    @cherrypy.expose
    def index(self, **params):
        # Render /create page
        initial_data = {'user':cherrypy.session.get('user')}
        return cache.get('layout').render({
            'page_body':cache.getRaw('create'),
            'account_url': '/api/auth/logout',
            'account_action': 'Log Out',
            'initial_data':json.dumps(initial_data)
        })
