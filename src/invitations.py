""" This file handles anything related to invitations to join a project """
import cherrypy
import json
import requests
from datetime import date

class InvitationHandler(object):
    """ This class handles user's invitation to join a project """
    # This is domain for calling notifications' API
    # Currently set to dev's domain (http://localhost:8080)
    # Will be changed to http://teamseek.io in the future when hosting
    domain = 'http://localhost:8080'

    # Set notification type for requesting
    notification_type = 2

    # Allowed actions
    _ACTION = {
        # [GET] method's actions
        '_GET': {
            # Getting user's previous sent invitations 
            'my_invitations': '',
            # Checking if a particular user has been invited to a particular project
            'is_invited': ''
        },
        # [POST] method's actions
        '_POST': {
            # Accepting an invitation
            'accept': '',
            # Denying an invitation
            'deny': ''
        },
        # [PUT] method's actions
        '_PUT': {
            # Sending invitation
            'new_invitation': ''
        }
    }

    def __init__(self, db=None):
        """ Initializing /api/invitations/ """
        if db:
            self.db = db
            self.cur = db.connection.cursor()
        else:
            print "invitations.py >> Error: Invalid database connection"

    @cherrypy.expose
    def index(self, **params):
        """ Forward HTTP requests to its rightful handler """
        # Check if user's logged in
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})

        # Get http method
        http_method = getattr(self, cherrypy.request.method)
        return http_method(**params)

    @cherrypy.tools.accept(media='text/plain')
    def GET(self, **params):
        """
        Handles pulling invitations from database

        params: i.e. {'action': 'my_invitations'}
                i.e. {'action': 'is_invited', 'user_id': '1', 'project_id': '3'}
        return: list of invitations
        """
        # Check if everything is provided
        if 'action' not in params:
            return json.dumps({'error': 'Not enough data'})

        # Check if action is allowed to perform
        if params['action'] not in self._ACTION['_GET']:
            return json.dumps({'error': 'Action is not allowed'})

        # Form query for database 
        query = """
                SELECT id, sender_id, (SELECT username FROM users WHERE user_id = sender_id), project_id, 
                       (SELECT title FROM project_info WHERE project_info.project_id = invitations.project_id),
                       recipient_id, 
                       (SELECT username FROM users WHERE user_id = recipient_id),
                       status, sent_date 
                FROM invitations
                
                """

        # If user is requesting his/her previous sent invitations
        if params['action'] == 'my_invitations':
            query += "WHERE sender_id = (SELECT user_id FROM users WHERE username = %s);"
            query_params = (cherrypy.session['user'], )

        # If user is checking if he's invited (used to display invite button)
        if params['action'] == 'is_invited':
            query += "WHERE recipient_id = %s AND project_id = %s;"
            query_params = (params['user_id'], params['project_id'], )

        self.cur.execute(query, query_params)
        invitations = format_invitations(self.cur.fetchall())
        return json.dumps(invitations, indent=4)

    @cherrypy.tools.accept(media='text/plain')
    def POST(self, **params):
        """
        Handles accepting, denying invitations

        params: i.e. {'action': 'accept', 'invitation_id': '1', 'notification_id': '2'} 
                i.e. {'action': 'deny', 'invitation_id': '1', 'notification_id': '2'}
        return: {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'invitation_id' not in params or \
           'notification_id' not in params: 
            return json.dumps({'error': 'Not enough data'})

        # Make sure that the actions are allowed
        if params['action'] not in self._ACTION['_POST']:
            return json.dumps({'error': 'Action is not allowed'})

        status = 'denied'
        if params['action'] == 'accept':
            status = 'accepted'

        # Form a query for database
        query = """
                DO $$
                DECLARE
                    LoggedUser VARCHAR;
                    RecipientName VARCHAR;
                    RecipientId INT;
                    ProjectID INT;
                    in_status TEXT;
                BEGIN
                LoggedUser = %s;
                in_status = %s;
                SELECT user_id, username INTO RecipientId, RecipientName FROM users WHERE username = LoggedUser;

                UPDATE invitations 
                SET status = in_status 
                WHERE id = %s AND recipient_id = RecipientId
                RETURNING project_id INTO ProjectID;
                
                IF in_status = 'accepted' THEN
                    INSERT INTO project_members (project_id, member) 
                    VALUES (ProjectID, RecipientName);
                END IF;
                END
                $$
                """
        self.cur.execute(query,(
                                cherrypy.session['user'],
                                status, 
                                params['invitation_id'],  
                               )) 

        # Apply changes to database
        self.db.connection.commit()

        # Trigger notification
        request_params = {
            'action': 'delete',
            'id': params['notification_id']
        }
        response = requests.post('{0}/api/notifications/'.format(self.domain), params=request_params)
        return json.dumps(response.text)

    @cherrypy.tools.accept(media='text/plain')
    def PUT(self, **params):
        """
        Handle sending out invitations.

        params: i.e. {'action': 'new_invitation', 'project_id': '1', 'user_id': '1'}
        return: i.e. {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'project_id' not in params or \
           'user_id' not in params:
            return json.dumps({'error': 'Not enough data'})

        # Make sure that action is allowed
        if params['action'] not in self._ACTION['_PUT']:
            return json.dumps({'error': 'Action is not allowed'})

        # Form a query for database
        query = """
                CREATE OR REPLACE FUNCTION my_function()
                    RETURNS INT AS 
                $BODY$
                DECLARE 
                    RecipientId INT;
                    SenderId INT;
                    invitation_id INT;
                    ProjectId INT;
                BEGIN
                    RecipientId = %s;
                    ProjectId = %s;
                    SELECT users.user_id INTO SenderId FROM users WHERE username = %s;

                    PERFORM id 
                    FROM invitations 
                    WHERE project_id = ProjectId AND recipient_id = RecipientId;

                    IF NOT FOUND THEN
                        INSERT INTO invitations (recipient_id, sender_id, project_id, sent_date) 
                        VALUES (RecipientId, SenderId, ProjectId, %s) RETURNING id INTO invitation_id;
                    END IF;

                    RETURN invitation_id;
                END;
                $BODY$ LANGUAGE plpgsql;

                SELECT my_function();
                """
        query_params = (
            params['user_id'],
            params['project_id'],
            cherrypy.session['user'],
            date.today(), )
        self.cur.execute(query, query_params)

        # Grab returned values from database
        recipient_id = params['user_id']
        project_id = params['project_id']
        invitation_id = self.cur.fetchall()[0][0] 

        # If the invitation has already existed in database
        # return an error
        if not invitation_id:
            return json.dumps({"error": "This user has been invited!"})
        
        # Apply changes to database
        self.db.connection.commit()
        
        # Trigger notificiation
        request_params = {
            'action': 'new_notification',
            'type_id': self.notification_type, 
            'recipient_id': recipient_id,
            'sender_id': invitation_id 
        }
        response = requests.put('{0}/api/notifications/'.format(self.domain), params = request_params)
        return json.dumps(response.text)

    @cherrypy.tools.accept(media='text/plain')
    def DELETE(self, **params):
        return json.dumps({'error': 'Currently not supported'})

######################
# Helper Functions   #
######################

def format_invitations(fetch = None, notification=False):
    # Initialize an empty list
    invitations = []

    # Start formatting invitations into a list
    for item in fetch:
        dict = {}
        dict['invitation_id'] = item[0]
        dict['sender_id'] = item[1]
        dict['sender_username'] = item[2]
        dict['project_id'] = item[3]
        dict['project_title'] = item[4]
        dict['recipient_id'] = item[5]
        dict['recipient_username'] = item[6]
        dict['status'] = item[7]
        dict['sent_date'] = item[8].strftime('%m-%d-%Y')
        if notification:
            dict['notification_id'] = item[9]
        invitations.append(dict)

    return invitations
