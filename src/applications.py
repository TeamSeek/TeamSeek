""" This file handles anything that comes to applications
    including apply for project, accept and deny applications.
    
    This file also triggers notification for new applications.
"""
import cherrypy
import json
import requests
from datetime import date


class ApplicationHandler(object):
    """ Object for project's applications """

    def __init__(self, db=None):
        """ Run these instructions when project is initialized """
        # Check if database is passed in
        if db:
            self.notification_type = '1'
            self.db = db
            self.cur = db.connection.cursor()
        else:
            print "applications.py >> Error: Invalid database connection"

    @cherrypy.expose
    def index(self, **params):
        """ Forwarding HTTP requests to the right request handler """
        # Check if user's logged in
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})

        # Forwarding to the right request handler
        http_method = getattr(self, cherrypy.request.method)
        return http_method(**params)

    @cherrypy.tools.accept(media="text/plain")
    def GET(self, **params):
        return json.dumps({"error": "Currently not supported"})

    @cherrypy.tools.accept(media="text/plain")
    def POST(self, **params):
        """
        Accept or Deny an application and trigger new notification

        Also handle user's working-on projects and project's members

        params: i.e. {'action': 'edit_application', 'id': 'application id', 'status': 'pending/denied/approved'}
        return: i.e. {} if successful, {'error': 'some error' if failed'}
        """
        # Check if everything is provided
        if 'action' not in params or \
           'id' not in params or \
           'status' not in params:
            return json.dumps ({'error': 'Not enough data'})

        # Edit the application
        query = """
                UPDATE applications SET status = %s WHERE id = %s RETURNING 
                """

        return json.dumps({"error": "Currently not supported"})

    @cherrypy.tools.accept(media="text/plain")
    def PUT(self, **params):
        """ 
        Insert a new application and trigger new notification
        
        params: i.e. {'action': 'new_application', 'project_id': '1'}
        return: {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'project_id' not in params:
            return json.dumps({'error': 'Not enough data'})

        username = cherrypy.session['user']
        # Add new applications to database
        # If accepted is not provided meaning that 
        # the application is still pending
        query = """INSERT INTO applications (project_id, user_id, date_applied)
                   VALUES (%s, (SELECT user_id FROM users WHERE username = %s), %s) 
                   RETURNING id, (SELECT user_id 
                                                   FROM users 
                                                   WHERE username = (SELECT owner 
                                                                     FROM project_info 
                                                                     WHERE project_info.project_id = applications.project_id));
                """
        self.cur.execute(query, (params['project_id'], username, date.today(), ))
        # Grab ID from the new application
        fetch = self.cur.fetchall()
        sender_id = fetch[0][0]
        recipient_id = fetch[0][1]
        # Trigger notification
        request_params = {  'action': 'new_application',
                    'type_id': self.notification_type,
                    'recipient_id': recipient_id,
                    'sender_id': sender_id
                    }
        response = requests.put('http://localhost:8080/api/notifications/', params=request_params)
        print response.text
        # Apply changes to database
        self.db.connection.commit()
        return json.dumps({})

    @cherrypy.tools.accept(media="text/plain")
    def DELETE(self, **params):
        return json.dumps({"error": "Currently not supported"})
