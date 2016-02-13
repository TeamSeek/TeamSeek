""" This file handles anything related to invitations to join a project """
import cherrypy
import json
from datetime import date
import requests

class InvitationHandler(object):
    """ This class handles user's invitation to join a project """
    # Set notification type for requesting
    notification_type = 2

    # Allowed actions
    _ACTION = {
        # [GET] method's actions
        '_GET': {
            # Getting a history of who the user has invited
            'my_invitations': '',
            # Getting user's received invitations 
            'get_invitations': '',
            # Checking if the user has been invited
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
                i.e. {'action': 'get_invitations', 'ids': list of invitation ids}
        return: {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params:
            return json.dumps({'error': 'Not enough data'})

        # Check if action is allowed to perform
        if params['action'] not in self._ACTION['_GET']:
            return json.dumps({'error': 'Action is not allowed'})

        # Form query for database 
        query = """
                SELECT id, project_id, 
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

        # If user is requesting invitiations (based on a list of invitiation IDs, may be used for notifications)
        if params['action'] == 'get_invitations':
            query += "WHERE id IN %s;"
            query_params = (tuple(params['ids']), )

        self.cur.execute(query, query_params)
        invitations = format_invitations(self.cur.fetchall())
        return json.dumps(invitations, indent=4)

    @cherrypy.tools.accept(media='text/plain')
    def POST(self, **params):
        """
        Handles accepting, denying invitations

        params: i.e. {'action': 'accept', 'invitation_id': '1'} 
                i.e. {'action': 'deny', 'invitation_id': '1'}
        return: {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'invitation_id' not in params: 
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
                BEGIN
                
                LoggedUser = %s;

                SELECT user_id, username INTO RecipientId, RecipientName FROM users WHERE username = LoggedUser;

                UPDATE invitations 
                SET status = %s 
                WHERE id = %s AND recipient_id = RecipientId
                RETURNING project_id INTO ProjectID;

                INSERT INTO project_members (project_id, member) 
                VALUES (ProjectID, RecipientName);

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
        return json.dumps({})

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

        # Apply changes to database
        self.db.connection.commit()
        return json.dumps({})

    @cherrypy.tools.accept(media='text/plain')
    def DELETE(self, **params):
        return json.dumps({'error': 'Currently not supported'})

######################
# Helper Functions   #
######################

def format_invitations(fetch = None):
    # Initialize an empty list
    invitations = []

    # Start formatting invitations into a list
    for item in fetch:
        dict = {}
        dict['invitation_id'] = item[0]
        dict['project_id'] = item[1]
        dict['project_title'] = item[2]
        dict['recipient_id'] = item[3]
        dict['recipient_username'] = item[4]
        dict['status'] = item[5]
        dict['sent_date'] = item[6].strftime('%m-%d-%Y')
        invitations.append(dict)

    return invitations
