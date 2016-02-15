""" This file handles all notifications functions """
import cherrypy
import json
import applications
import invitations
from datetime import date

class NotificationHandler(object):
    """ This class handles adding, deleting, editing, and getting notifications """
    # Mapping actions for the HTTP requests
    _ACTION = {
        '_GET': {
            'my_notifications': ''
        },
        '_POST': {
            'read': ['read', True],
            'unread': ['read', False],
            'delete': ['deleted', True]
        },
        '_PUT': {
            'new_notification': ''
        },
        '_DELETE': {
            'action_here': 'not implemented'
        }
    }

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
        """
        Pulling notifications from database

        params: i.e. {'action': 'my_notifications', 'type': 'application'}
        return: a list of notifications
        """
        # Check if everything is provided
        if 'action' not in params or \
           'type' not in params:
            return json.dumps({'error': 'Not enough data'})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_GET']:
            return json.dumps({'error': 'Action is not allowed'})
        
        # Form a query for database
        notifications = []
        # If the user is requesting applications
        if params['type'] == 'application':
            notification_type = 1
            query = """
                    SELECT applications.id, project_id,
                           (SELECT title FROM project_info WHERE project_id = applications.project_id),
                           applicant_id, (SELECT username FROM users WHERE user_id = applicant_id),
                           status, date_applied, notifications.id
                    FROM notifications 
                    INNER JOIN applications ON applications.id = notifications.sender_id
                    WHERE recipient_id = (SELECT user_id 
                                          FROM users 
                                          WHERE username = %s) 
                    AND type_id = %s AND deleted = False AND read = False;
                    """
            self.cur.execute(query, (cherrypy.session['user'], notification_type, ))
            fetch = self.cur.fetchall()
            notifications = applications.format_application_details(fetch=fetch, notification=True)

        # If the user is requesting invitations
        if params['type'] == 'invitation':
            notification_type = 2
            query = """
                    SELECT invitations.id, invitations.sender_id,
                           (SELECT username FROM users WHERE user_id = invitations.sender_id),
                           project_id, 
                           (SELECT title FROM project_info WHERE project_info.project_id = invitations.project_id),
                           invitations.recipient_id, (SELECT username FROM users WHERE user_id = invitations.recipient_id),
                           status, sent_date, notifications.id
                    FROM notifications
                    INNER JOIN invitations ON invitations.recipient_id = notifications.recipient_id
                    WHERE notifications.recipient_id = (SELECT user_id FROM users WHERE username = %s)
                    AND type_id = %s AND deleted = False AND read = False;
                    """
            self.cur.execute(query, (cherrypy.session['user'], notification_type, ))
            fetch = self.cur.fetchall()
            notifications = invitations.format_invitations(fetch=fetch, notification=True)

        return json.dumps(notifications, indent=4)

    @cherrypy.tools.accept(media="text/plain")
    def POST(self, **params):
        """ 
        Mark notification as read/delete
        
        params: i.e. {'action': 'read', 'id': 'notification id'}
                i.e. {'action': 'delete', 'id': 'notification id'}
                i.e. {'action': 'unread', 'id': 'notification id'}
        return: i.e. {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'id' not in params:
            return json.dumps({'error': 'Not enough data'})
        
        # Check if action is allowed
        if params['action'] not in self._ACTION['_POST']:
            return json.dumps({'error': 'Action is not allowed'})

        # Grab everthing we need for query using _ACTION mapping
        table = self._ACTION['_POST'][params['action']][0]
        value = self._ACTION['_POST'][params['action']][1]

        # Form a query for database
        query = "UPDATE notifications SET {0} = {1} WHERE id = %s;".format(table, value)
        self.cur.execute(query, (params['id'], ))
        # Apply changes to database
        self.db.connection.commit()

        return json.dumps({})

    @cherrypy.tools.accept(media="text/plain")
    def PUT(self, **params):
        """
        Add notifications into database

        params: i.e. {'action': 'new_notification', 'type_id': '1', 'recipient_id': '1', 'sender_id': '2'}
        return: i.e. {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'recipient_id' not in params or \
           'sender_id' not in params:
            return json.dumps({'error': 'Not enough data'})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_PUT']:
            return json.dumps({'error': 'Action is not allowed'})

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
