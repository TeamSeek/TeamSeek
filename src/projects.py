"""
This file handles anything related to projects
such as editing project's details, adding projects, getting project's details
"""

import psycopg2.extras
import cherrypy
import json
from datetime import date
from datetime import datetime

""" Handling projects """
class ProjectHandler(object):
    """ Initializing class with ProjectHandler(database) to use """

    # actions that you can use for the HTTP requests
    # Each action is associated with their table and columns
    # i.e 'edit_title': ['table name', 'column name']
    _ACTION = {
        # [GET] Getting project's details
        '_GET': {
            'project_details': [], 
            'my_projects': [], 
            'working_on': [],
            'project_cmts': ''
        },
        # [POST] Editing project's details
        # params: action, project_id, data
        '_POST': {
            'edit_progress': ['project_info', 'progress'],
            'edit_title': ['project_info', 'title'],
            'edit_short_desc': ['project_info', 'short_desc'],
            'edit_long_desc': ['project_info', 'long_desc'],
            'edit_update': ['project_extras', 'update'],
            'edit_git_link': ['project_extras', 'git_link']
        },
        # [PUT] creating new projects or adding new project details
        '_PUT': {
            'new_project': [],
            'add_member': ['project_members', 'member'],
            'add_skill': ['project_skills', 'skill'],
            'add_cmt': [] 
        },
        # [DELETE] Deleting project or project's details
        '_DELETE': {
            'delete_skill': ['project_skills', 'skill'],
            'delete_member': ['project_members', 'member'],
            'delete_cmt': ''
        }
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
    def default(self, *path, **params):
        """ Forward HTTP methods to the correct function """
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
            i.e {'action': 'my_projects', 'user': 'username'}
            i.e {'action': 'project_cmts', 'project_id': '1'}
        """
        full = False
        # If owner is provided
        if params['action'] != 'project_cmts':
            user = params['user']

        # Check if everything is provided
        if 'action' not in params and \
           ('title' not in params or 'user' not in params) and \
           'project_id' not in params:
            return json.dumps({"error": "Not enough data"})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_GET']:
            return json.dumps({'error': 'Action is not allowed'})

        # Create new dictionary cursor
        dCur = self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
        # If grabbing project's comments
        if params['action'] == 'project_cmts':
            # Use helper function at the end of this file
            result = fetch_comment(dCur, params['project_id'])
            return result

        # Getting project's details
        query = """
                SELECT	project_id, title, owner, short_desc,
                        to_char(last_edit, 'MM-DD-YY') as last_edit,
                        to_char(posted_date, 'MM-DD-YY') as posted_date,
                        (SELECT update FROM project_extras WHERE project_id=project_info.project_id),
                        (SELECT git_link FROM project_extras WHERE project_id=project_info.project_id),
                        array(SELECT skill FROM project_skills WHERE project_id=project_info.project_id) AS project_skills,
                        array(SELECT member FROM project_members WHERE project_id=project_info.project_id) AS project_members,
                        long_desc, progress
                FROM    project_info
                {0}
                ORDER BY posted_date DESC;
                """
        query_format = "WHERE owner = %s AND title LIKE %s"

        # If fetching projects "user" is currently a member of
        if params['action'] == 'working_on':
            query_format = "WHERE project_id in (select project_id from project_members where member = %s) -- %s"

        # If fetching a particular project details
        if 'project_details' == params['action']:
            dCur.execute(query.format(query_format), (params['user'], params['title']))
            result = dCur.fetchone()
            if not result:
                raise cherrypy.HTTPError(404)
        # If fetching all projects from an owner
        else:
            dCur.execute(query.format(query_format), (user,'%'))
            result = dCur.fetchall()

        return json.dumps(result, indent = 4)

    """ [POST] request handler """
    def POST(self, **params):
        """
        Editing project's details including:
            title, short_desc, long_desc, update, git_link

        :params : See _ACTION for a list of actions
            i.e {'action': 'edit_title', 'project_id': '4', 'data': 'change data'}
        :return : {} for successful, {"error": "some error"} for failed
        """
        # Check if user's logged in
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})

        # Check that everything is right
        if 'action' not in params or \
           'project_id' not in params or \
           'data' not in params:
            return json.dumps({"error": "Not enough data"})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_POST']:
            return json.dumps({'error': 'Action is not allowed'})

        # Get everything needed to edit
        action = params['action']
        # Mapping table using _ACTION variable above
        table = self._ACTION['_POST'][action][0]
        # Mapping column using _ACTION variable above
        column = self._ACTION['_POST'][action][1]
        # Get project_id from params
        project_id = params['project_id']
        # Get data from params
        data = params['data']

        # Check if title has been used, it's a unique thing for each user.
        if params['action'] == 'edit_title':
            query = "SELECT * FROM project_info WHERE owner = %s and title = %s"
            self.cur.execute(query, (cherrypy.session['user'], params['data'], ))
            if self.cur.fetchall():
                return json.dumps({"error": "Title has been used"})

        # If editing values
        # only edit value if the currently logged in user is the project's owner
        query = """
                DO $$
                    DECLARE
                        in_data VARCHAR;
                        projectId INT;
                        in_owner VARCHAR;
                    BEGIN
                        in_data = %s;
                        projectId = %s;
                        in_owner = %s;
                        UPDATE {0} SET {1} = in_data WHERE project_id=projectId AND owner = in_owner;
                        UPDATE project_info SET last_edit = %s WHERE project_id = projectId;
                    END;
                $$
                """
        self.cur.execute(query.format(table, column), (data, project_id, cherrypy.session['user'], date.today()))
        # Commit the changes to database
        self.db.connection.commit()
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
            i.e. {'action': 'add_cmt', 'data': 'Comment', 'project_id': '1', 'parent_id': '0'}

        :return : {} if successful, {"error": "some error"}
        """
        # Check if user's logged in
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})

        # Check if everything is provided
        if 'action' not in params or \
          ('title' not in params and
           ('data' not in params or 'project_id' not in params)):
            return json.dumps({"error": "Not enough data"})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_PUT']:
            return json.dumps({'error': 'Action is not allowed'})
        
        # If action is add comments
        if params['action'] == 'add_cmt':
            dCur = self.db.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            msg = add_comment(dCur, params['data'], params['project_id'], params['parent_id'], )
            # Apply changes to database
            self.db.connection.commit()
            return json.dumps(msg)

        # If creating new project
        if 'new_project' == params['action']:
            project_id = add_new_project(self.cur, cherrypy.session['user'], params['title'])
            # Apply changes
            self.db.connection.commit()
            return json.dumps({'project_id':project_id[0]})

        # Add member and skill to database
        # Prepare everything we need
        table = self._ACTION['_PUT'][params['action']][0]
        column = self._ACTION['_PUT'][params['action']][1]

        # Adding based on the action provided
        # only add member or skill if the current logged-in user
        # is the owner of the project
        query = """
                DO $$
                    DECLARE
                        projectId INT;
                    BEGIN
                        project_id = %s;
                        PERFORM project_id FROM project_info WHERE project_id = projectId AND owner = %s;
                        IF FOUND THEN
                            INSERT INTO {0} (project_id, {1}) VALUES (projectId, %s);
                        END IF;
                    END;
                $$
                """
        self.cur.execute(query.format(table, column), (params['project_id'], cherrypy.session['user'], params['data'], ))
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
            i.e. {'action': 'delete_cmt', 'id': '1'}
        :return: {} for successful. {'error': 'some error'} for failed
        """
        # Check if user's logged in
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})

        # Check if everything is provided
        if 'action' not in params or \
           ('id' not in params and ('data' not in params or 'project_id' not in params)):
            return json.dumps({"error": "Not enough data"})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_DELETE']:
            return json.dumps({'error': 'Action is not allowed'})

        # If requesting to delete comment
        # only if the current logged in user is the owner of the project
        if params['action'] == 'delete_cmt':
            query = """
                    DELETE FROM project_cmts 
                    WHERE id = %s AND poster_id = (SELECT user_id FROM users WHERE username = %s);
                    """
            self.cur.execute(query, (params['id'], cherrypy.session['user'] ))
            self.db.connection.commit()
            return json.dumps({})

        # Prepare everything we need
        table = self._ACTION['_DELETE'][params['action']][0]
        column = self._ACTION['_DELETE'][params['action']][1]
        # Delete data (skill, member) from project
        # only if the current logged in user is the owner of the project
        query = """
                DO $$
                    DECLARE
                        projectId INT;
                    BEGIN
                        projectId = %s;
                        PERFORM project_id FROM project_info WHERE project_id = projectId AND owner = %s;
                        IF FOUND THEN
                            DELETE FROM {0} WHERE {1} = %s AND project_id = projectId;
                        END IF;
                    END;
                $$
                """
        self.cur.execute(query.format(table, column), (cherrypy.session['user'], params['project_id'], params['data'], ))
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
    fetch_id = """
            SELECT project_id FROM project_info WHERE title = %s and owner = %s;
            """
    cur.execute(query, (title, owner, title, owner, date.today(), title, owner, ))
    cur.execute(fetch_id, (title, owner))
    project_id = cur.fetchone()
    return project_id

# Adding comments
def add_comment(dCur=None, cmt=None, project_id=None, parent_id=None):
    """ Adding comment into a particular project """
    # If comment is blank, do not add!
    if not cmt:
        return json.dumps({"error": "Comment cannot be blank"})

    # Start adding comment into database
    query = """
            INSERT INTO project_cmts (parent_id, project_id, poster_id, cmt, cmt_time)
            VALUES (%s, %s, (SELECT user_id FROM users WHERE username = %s), %s, %s) RETURNING id;
            """
    dCur.execute(query, (parent_id, project_id, cherrypy.session['user'], cmt, datetime.now(), ))
    msg = dCur.fetchone()
    return msg

# Fetching comments
def fetch_comment(dCur=None, project_id=None):
    query = """
            SELECT  p.id, poster_id as user_id,
                    (SELECT username FROM users WHERE user_id = poster_id),
                    avatar, full_name,
                    cmt as comment, 
                    to_char(cmt_time, 'MM-DD-YY HH:MI:SS') as cmt_time, 
                    array((SELECT row_to_json(d) FROM (SELECT c.id, c.poster_id as user_id,
                                                        (SELECT username FROM users WHERE user_id = poster_id),
                                                        avatar, full_name,
                                                        c.cmt as comment, 
                                                        to_char(c.cmt_time, 'MM-DD-YY HH:MI:SS') as cmt_time
                                                        FROM project_cmts c
                                                        LEFT JOIN user_extras ON (user_id = poster_id)
                                                        WHERE parent_id = p.id
                                                        ORDER BY cmt_time DESC
                                                      ) d )) as c_comments
            FROM project_cmts p
            LEFT JOIN user_extras ON (user_id = poster_id)
            WHERE project_id = %s AND parent_id = 0
            ORDER BY cmt_time DESC;
            """
    dCur.execute(query, (project_id, ))
    # Get results from database returned data
    results = dCur.fetchall()
    return json.dumps(results, indent = 4)
