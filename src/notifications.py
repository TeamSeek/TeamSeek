""" This file handles all notifications functions """
import cherrypy
import json
from datetime import date

class NotificationHandler(object):
    """ This class handles adding, deleting, editing, and getting notifications """

    def __init__(self, db=None):
        """ Initializing object """
        if db:
            self.db = db
            self.cur = db.connection.cursor()
        else:
            print "notifications.py >> Error: Invalid database connection"
    
    @cherrypy.expose
    def index(self, **params):
        """ Forward HTTP requests to its rightful place """
        # Check if user's logged in
        #if 'user' not in cherrypy.session:
        #    return json.dumps({"error": "You shouldn't be here"})

        # Forward HTTP requests
        http_method = getattr(self, cherrypy.request.method)
        return http_method(**params)

    @cherrypy.tools.accept(media="text/plain")
    def GET(self, **params):
        return json.dumps({'error': 'Currently not supported'})

    @cherrypy.tools.accept(media="text/plain")
    def POST(self, **params):
        return json.dumps({'error': 'Currently not supported'})

    @cherrypy.tools.accept(media="text/plain")
    def PUT(self, **params):
        """
        Add notifications into database

        params: i.e. {'action': 'new_application', 'type_id': '1', 'recipient_id': '1', 'sender_id': '2'}
        return: i.e. {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'recipient_id' not in params or \
           'sender_id' not in params:
            return json.dumps({'error': 'Not enough data'})

        # Form query for adding notification into database
        query = """
                INSERT INTO notifications (recipient_id, sender_id, type_id, created_date)
                VALUES (%s, %s, %s, %s);
                """
        self.cur.execute(query, (params['recipient_id'], params['sender_id'], params['type_id'], date.today(), ))
        # Apply changes to database
        self.db.connection.commit()
        return json.dumps({})

    @cherrypy.tools.accept(media="text/plain")
    def DELETE(self, **params):
        return json.dumps({'error': 'Currently not supported'})
