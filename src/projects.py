"""
This file handles anything related to projects
such as editing project's details, adding projects, getting project's details
"""

import psycopg2.extras
import cherrypy
import json
from datetime import date

""" Handling projects """
class ProjectHandler(object):
    """ Initializing class with ProjectHandler(database) to use """

    # actions that you can use for the HTTP requests
    # Each action is associated with their table and columns
    # i.e 'edit_title': ['table name', 'column name']
    _ACTION = {
        # [GET] Getting project's details
        'project_details': [],  # params: action, title, user
        'my_projects': [],      # params: action, owner (optional)
        # [POST] Editing project's details
        # params: action, project_id, data
        'edit_title': ['project_info', 'title'],
        'edit_short_desc': ['project_info', 'short_desc'],
        'edit_long_desc': ['project_info', 'long_desc'],
        'edit_update': ['project_extras', 'update'],
        'edit_git_link': ['project_extras', 'git_link'],
        # [PUT] creating new projects or adding new project details
        'new_project': [],
        'add_member': ['project_members', 'member'],
        'add_skill': ['project_skills', 'skill'],
        # [DELETE] Deleting project or project's details
        'delete_skill': ['project_skills', 'skill'],
        'delete_member': ['project_members', 'member']
    }

    def __init__(self, db=None):
        """ Initializing variables for object """
        if db:
            self.db = db
            self.cur = db.connection.cursor()
        else:
            print "projects.py >> Error: Invalid database connection"

    """ Main page """
    @cherrypy.expose
    def index(self, **params):
        """ Forward HTTP methods to the correct function """
        # Check if user's logged in
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})
        # Forward HTTP methods
        http_method = getattr(self, cherrypy.request.method)
        return http_method(**params)

    """ [GET] request handler """
    @cherrypy.tools.accept(media='text/plain')
    def GET(self, **params):
        """
        Pulling user's details

        :params: Checking _ACTION for a list of action
            i.e {'action': 'project_details', 'title': 'some title', 'user': 'some users'}
            i.e {'action': 'my_projects'}
        """
        full = False
        # Grab user that's logged on
        user = cherrypy.session['user']

        # If owner is provided
        if 'owner' in params:
            user = params['owner']

        # Check if everything is provided
        if 'action' not in params and \
           ('title' not in params or 'user' not in params):
            return json.dumps({"error": "Not enough data"})

        # Getting project's details
        query = """
                SELECT	project_id, title, owner, short_desc,
                        to_char(last_edit, 'MM-DD-YY') as last_edit,
                        to_char(posted_date, 'MM-DD-YY') as posted_date,
                        (SELECT update FROM project_extras WHERE project_id=project_info.project_id),
                        (SELECT git_link FROM project_extras WHERE project_id=project_info.project_id),
                        array(SELECT skill FROM project_skills WHERE project_id=project_info.project_id),
                        array(SELECT member FROM project_members WHERE project_id=project_info.project_id),
                        long_desc, progress
                FROM    project_info
                WHERE owner = %s AND title LIKE %s
                """

        # Create new dictionary cursor
        dCur = self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # If fetching a particular project details
        if 'project_details' == params['action']:
            dCur.execute(query, (params['user'], params['title']))
            result = dCur.fetchone()
            if not result:
                raise cherrypy.HTTPError(404)
        # If fetching all projects from an owner
        else:
            dCur.execute(query, (user,'%'))
            result = dCur.fetchall()

        return json.dumps(result)

    """ [POST] request handler """
    def POST(self, **params):
        """
        Editing project's details including:
            title, short_desc, long_desc, update, git_link

        :params : See _ACTION for a list of actions
            i.e {'action': 'edit_title', 'project_id': '4', 'data': 'change data'}
        :return : {} for successful, {"error": "some error"} for failed
        """
        # Check that everything is right
        if 'action' not in params or \
           'project_id' not in params or \
           'data' not in params:
            return json.dumps({"error": "Not enough data"})

        # Get everything needed to edit
        action = params['action']
        # Mapping table using _ACTION variable above
        table = self._ACTION[action][0]
        # Mapping column using _ACTION variable above
        column = self._ACTION[action][1]
        # Get project_id from params
        project_id = params['project_id']
        # Get data from params
        data = params['data']

        # Check if title has been used, it's a unique thing for each user.
        if params['action'] == 'edit_title':
            query = "SELECT * FROM user_info WHERE owner = %s and title = %s"
            self.cur.execute(query, (cherrypy.session['user'], params['title'], ))
            if self.cur.fetchall():
                return json.dumps({"error": "Title has been used"})

        # If editing values
        # Execute this command
        # Don't worry about SQL Injection because
        # table and column are mapped, not user input
        query = "UPDATE " + table + " SET " + column + " = %s WHERE project_id=%s;"
        self.cur.execute(query, (data, project_id, ))
        # Commit the changes to database
        self.db.connection.commit()
        # Update last_edit column
        update_last_edit(self.cur, project_id)
        # Apply changes to database
        self.db.connection.commit()

        # If everything succeeded, return nothing
        return json.dumps({})

    """ [PUT] request handler """
    def PUT(self, **params):
        """
        Adding new data into database

        :params : Check _ACTION to know what option you have
            i.e. {'action': 'new_project', 'title': 'new title'}
            i.e. {'action': 'add_member', 'data': 'new member', 'project_id': '1'}
            i.e. {'action': 'add_skill', 'data': 'new skill', 'project_id': '1'}

        :return : {} if successful, {"error": "some error"}
        """
        # Check if everything is provided
        if 'action' not in params or \
          ('title' not in params and
          ('member' not in params or 'skill' not in params) and
           'project_id' not in params):
            return json.dumps({"error": "Not enough data"})

        # If creating new user
        if 'new_project' == params['action']:
            add_new_project(self.cur, cherrypy.session['user'], params['title'])
            # Apply changes
            self.db.connection.commit()
            return json.dumps({})

        # Add member and skill to database
        # Prepare everything we need
        table = self._ACTION[params['action']][0]
        column = self._ACTION[params['action']][1]

        # Adding based on the action provided
        query = "INSERT INTO " + table + " (project_id, " + column + ") VALUES (%s, %s);"
        self.cur.execute(query, (params['project_id'], params['data'], ))
        # Apply changes to database
        self.db.connection.commit()

        return json.dumps({})

    """ [DELETE] request handler """
    def DELETE(self, **params):
        """
        Deleting details from project like: skill, member

        :param params: Check _ACTION above to find out options available
            i.e. {'action': 'delete_skill', 'data': 'javascript', 'project_id' = '1'}
            i.e. {'action': 'delete_member', 'data': 'gnihton', 'project_id' = '1'}
        :return: {} for successful. {'error': 'some error'} for failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'data' not in params or \
           'project_id' not in params:
            return json.dumps({"error": "Not enough data"})

        # Prepare everything we need
        table = self._ACTION[params['action']][0]
        column = self._ACTION[params['action']][1]
        # Delete data (skill, member) from project
        query = "DELETE FROM " + table + " WHERE " + column + " = %s AND project_id = %s"
        self.cur.execute(query, (params['data'], params['project_id'], ))
        # Apply changes to database
        self.db.connection.commit()
        return json.dumps({})

####################
# Helper functions #
####################

""" Formatting project details """
def format_project_details(full=False, cur=None, fetch=None):
    # Begin adding project into a list
    project_list = []     # List of projects
    for project in fetch:
        # Project's details
        dict = {'project_id': project[0],
                'title': project[1],
                'owner': project[2],
                'short_desc': project[3],
                'last_edit': str(project[4]),
                'posted_date': project[5].strftime('%m-%d-%Y'),
                'update': project[6],
                'git_link': project[7],
                'project_skills': project[8],
                'project_members': project[9]
                }
        if full:
            dict['long_desc'] = project[10]
        # Adding the project's details into the list
        project_list.append(dict)

    return project_list

""" Handle updating last_edit """
def update_last_edit(cur=None, project_id=None):
    query = "UPDATE project_info SET last_edit=%s WHERE project_id=%s"
    cur.execute(query, (date.today(), project_id, ))
    return

""" Adding new project """
def add_new_project(cur=None, owner=None, title=None):
    # Check if title has been used in this account
    # If it's not, add.
    query = """
            DO $$
            BEGIN
                PERFORM project_id FROM project_info WHERE title = %s and owner = %s;
                IF NOT FOUND THEN
                    INSERT INTO project_info (title, owner, posted_date) VALUES (%s, %s, %s);
                    INSERT INTO project_extras (project_id) VALUES ((SELECT project_id FROM project_info
                                                                    WHERE title = %s AND owner = %s));
                END IF;
            END
            $$
            """
    cur.execute(query, (title, owner, title, owner, date.today(), title, owner, ))
    return
