""" This file handles anything that comes to applications
    including apply for project, accept and deny applications.
"""
import cherrypy
import json
import requests
import psycopg2.extras
from datetime import date


class ApplicationHandler(object):
    """ Object for project's applications """
    # This is domain for calling notifications' API
    # Currently set to dev's domain (http://localhost:8080)
    # Will be changed to http://teamseek.io in the future when hosting
    domain = 'http://localhost:8080'

    # Notification type for application
    notification_type = 1

    # Only these _ACTIONs are allowed
    _ACTION = {
        # [GET] actions
        '_GET': {
            # Getting user's applications
            'my_applications': '',
            # Checking if a project has been applied
            'is_applied': '',
        },
        # [POST] actions
        '_POST': {
            # Approving an application (used for project's leader)
            'approve': '',
            # Denying an application (used for project's leader)
            'deny': ''
        },
        # [PUT] actions
        '_PUT': {
            # Sending out an application to the project's leader
            'new_application': '',
        }
    }

    def __init__(self, db=None):
        """ Run these instructions when project is initialized """
        # Check if database is passed in
        if db:
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
        """
        Handle pulling applications

        params: i.e. {'action': 'my_applications'}
                i.e. {'action': 'is_applied', 'project_id': '5'}
        return: a list of applications' details
        """
        # Check if everything is provided
        if 'action' not in params or params['action'] not in self._ACTION['_GET']:
            return json.dumps({'error': 'Not enough data'})

        if (not 'my_applications' == params['action']) and \
           ('ids' not in params and 'project_id' not in params):
            return json.dumps({'error': 'Not enough data'})
        # Form query for database

        query = """
                SELECT  id, project_id, 
                        (SELECT title FROM project_info WHERE project_info.project_id = applications.project_id), 
                        applicant_id, (SELECT username FROM users WHERE user_id = applicant_id), 
                        status, date_applied
                FROM applications

                """
        # If user is requesting his/her applications
        if 'my_applications' == params['action']:
            query_condition = "WHERE applicant_id = (SELECT user_id FROM users WHERE username = %s);"
            query_params = (cherrypy.session['user'], )
        # If user is requesting to check if she/he has already applied for a particular project
        else: 
            query_condition = """
                              WHERE applicant_id = (SELECT user_id FROM users WHERE username = %s)
                              AND project_id = %s; 
                              """
            query_params = (cherrypy.session['user'], params['project_id'], ) 

        # Append the condition to query
        query += query_condition
        # Send query to database
        self.cur.execute(query, query_params )
        # Format applications
        applications = format_application_details(fetch=self.cur.fetchall())
        return json.dumps(applications, indent=4)

    @cherrypy.tools.accept(media="text/plain")
    def POST(self, **params):
        """
        Accept or Deny an application         
        
        Also handle project's members

        params: i.e. {'action': 'approve', 'application_id': 'application id', 'notification_id': 'notification id'}
                i.e. {'action': 'deny', 'application_id': 'application id', 'notification_id': 'notification id'}
        return: {} if successful, {'error': 'some error' if failed'}
        """
        # Check if everything is provided
        if 'action' not in params or \
           'application_id' not in params or \
           'notification_id' not in params: 
            return json.dumps ({'error': 'Not enough data'})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_POST']:
            return json.dumps({'error': 'Action is not allowed'})

        # Edit the application
        status = 'denied'
        if params['action'] == 'approve':
            status = 'approved'

        query = """
                CREATE OR REPLACE FUNCTION edit_application()
                RETURNS INT AS
                $BODY$
                    DECLARE
                        in_status VARCHAR;
                        appID INT;
                        projectID INT;
                        applicantID INT;
                        notificationID INT;
                    BEGIN
                        in_status = %s;
                        appID = %s;

                        UPDATE applications 
                        SET status = in_status 
                        WHERE id = appID 
                        RETURNING applicant_id, project_id, (SELECT notifications.id 
                                                             FROM notifications 
                                                             WHERE notifications.sender_id = applications.id)
                        INTO applicantID, projectID, notificationID;

                        IF in_status = 'approved' THEN
                            INSERT INTO project_members (project_id, member)
                            VALUES (projectID, (SELECT username FROM users WHERE user_id = applicantID));
                        END IF;
                        
                        RETURN notificationID;
                    END;
                $BODY$ LANGUAGE plpgsql;
                
                SELECT edit_application();
                """
        self.cur.execute(query, (status, params['application_id'], ))
        # Apply changes to database
        self.db.connection.commit()

        # Grab the returned values from database
        fetch = self.cur.fetchone()
        notification_id = fetch[0]

        # Trigger notification
        request_params = {'action': 'delete', 'id': notification_id} 
        response = requests.post('{0}/api/notifications/'.format(self.domain), params=request_params)

        return json.dumps(response.text)

    @cherrypy.tools.accept(media="text/plain")
    def PUT(self, **params):
        """ 
        Insert a new application and trigger notification
        
        params: i.e. {'action': 'new_application', 'project_id': '1'}
        return: {} if successful, {'error': 'some error'} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'project_id' not in params:
            return json.dumps({'error': 'Not enough data'})
        
        # Check if action is allowed
        if params['action'] not in self._ACTION['_PUT']:
            return json.dumps({'error': 'Action is not allowed'})

        username = cherrypy.session['user']
        # Add new applications to database
        # If accepted is not provided meaning that 
        # the application is still pending
        query = """
                DROP FUNCTION my_function();
                CREATE OR REPLACE FUNCTION my_function()
                    RETURNS TABLE (sender_id INT, recipient_id INT) AS
                $BODY$
                DECLARE
                    projectId INT;
                    usrId INT;
                    applicationID INT;
                    ownerID INT;
                BEGIN
                    projectId = %s;
                    usrId = (SELECT user_id FROM users WHERE username=%s);

                    PERFORM id FROM applications WHERE project_id = projectId AND applicant_id = usrId;
                    IF NOT FOUND THEN 
                        RETURN QUERY
                            INSERT INTO applications (project_id, applicant_id, date_applied)
                            VALUES (projectId, usrId, %s)
                            RETURNING id AS sender_id, (SELECT user_id AS recipient_id
                                           FROM users 
                                           WHERE username = (SELECT owner 
                                                             FROM project_info 
                                                             WHERE project_id = applications.project_id));
                    END IF;
                END;
                $BODY$ LANGUAGE plpgsql;

                SELECT * FROM my_function(); 
                """
        dCur = self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        dCur.execute(query, (params['project_id'], username, date.today(), ))
        
        # Grab returned values from database
        fetch = dCur.fetchone()
        
        # If application has already existed
        # which means that fetch doesn't have any value
        # return an error
        if not fetch:
            return json.dumps({"error": "This user has already applied for this project!"})

        # Trigger notification
        request_params = {
            'action': 'new_notification', 
            'type_id': self.notification_type, 
            'recipient_id': fetch['recipient_id'], 
            'sender_id': fetch['sender_id']
        }
        response = requests.put('{0}/api/notifications/'.format(self.domain), params=request_params)
        # Apply changes to database
        self.db.connection.commit()

        return json.dumps(response.text)

    @cherrypy.tools.accept(media="text/plain")
    def DELETE(self, **params):
        return json.dumps({"error": "Currently not supported"})


##########################
# Helper functions       #
##########################
def format_application_details(fetch=None, notification=False):
    """ Formating applications into a list of dictionary """
    application_details = []
    for application in fetch:
        dict = {}
        dict['application_id'] = application[0]
        dict['project_id'] = application[1]
        dict['title'] = application[2]
        dict['applicant_id'] = application[3]
        dict['applicant_username'] = application[4]
        dict['status'] = application[5]
        dict['date_applied'] = application[6].strftime('%m-%d-%Y')
        if notification:
            dict['notification_id'] = application[7]
        application_details.append(dict)
    return application_details
