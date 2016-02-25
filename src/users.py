""" This file handles delete/edit/add users """

import cherrypy
import json
from datetime import date

""" Editing user class """
class UserHandler(object):
    """ Managing user's data """

    # List of actions that you can use to call HTTP requests
    # Format: {'action': [table, column(s)]}
    _ACTION = {
        # [GET] Getting user's details
        '_GET': {
            'user_details': []     # To get user's full details
        },
        # [POST] Editing user's details
        '_POST': {
            'edit_email': ['users', 'email'],
            'edit_full_name': ['user_extras', 'full_name'],
            'edit_bio': ['user_extras', 'bio'],
            'edit_avatar': ['user_extras', 'avatar'],
            'edit_skill_level': ['user_skills', 'level'],
            'edit_cur_city': ['user_locs', 'cur_city'],
            'edit_cur_state': ['user_locs', 'cur_state'],
            'edit_cur_country': ['user_locs', 'cur_country']
        },
        # [PUT] Adding username and email into database (first use)
        '_PUT': {
            'add_user': [],         # Add user into database (new users
            'add_skill': []        # Add new skill into user's details
        },
        # [DELETE] Removing user's details
        '_DELETE': {
            'delete_skill': ['user_skills', 'skill']      # delete user's old skill from database
        }
    }

    def __init__(self, db=None):
        """ Initializing UserHandler object """
        if db:
            self.db = db
            self.cur = db.connection.cursor()
        else:
            print "users.py >> Error: Invalid database connection"

    """ Forward HTTP methods"""
    @cherrypy.expose
    def index(self, **params):
        """ Forward HTTP requests to the right handler """
        # Make sure that user is logged in
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})
        # Forward HTTP requests
        http_method = getattr(self, cherrypy.request.method)
        return http_method(**params)

    """ GET request handler """
    @cherrypy.tools.accept(media='text/plain')
    def GET(self, **params):
        """
        Getting full user's details based on 'username'

        :param params: {'action': 'user_details', 'username': 'some username'}
        :return: all user details
        """
        if 'action' not in params or \
           'username' not in params:
                return json.dumps({"error": "Not enough data"})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_GET']:
            return json.dumps({'error': 'Action is not allowed'})

        # Fetch the user that has 'username'
        query = """
                SELECT  users.user_id, username, email, join_date,
                        (SELECT full_name FROM user_extras WHERE user_id = users.user_id),
                        (SELECT bio FROM user_extras WHERE user_id = users.user_id),
                        (SELECT avatar FROM user_extras WHERE user_id = users.user_id),
                        array(SELECT skill FROM user_skills WHERE user_skills.user_id = users.user_id),
                        array(SELECT level FROM user_skills WHERE user_skills.user_id = users.user_id)
                FROM users
                WHERE username = %s;
                """
        self.cur.execute(query, (params['username'], ))
        # Fetching the data from database
        fetch = self.cur.fetchall()
        # If nothing is found
        if not fetch:
            return json.dumps([])
        # Grab all user_details returned from 'fetch'
        user_details = format_user_details(full=True, fetch=fetch)
        # Return only 1 user detail because
        # the list will contain only 1 object
        return json.dumps(user_details[0], indent=4)

    """ POST request handler """
    def POST(self, **params):
        """
        Editing a particular user's detail

        :param params:  See _ACTION at the top of this file for list of actions
                        i.e. {'action': 'edit_email', 'data': 'example@example.com'}
                        i.e. {'action': 'edit_full_name', 'data': 'Full Name'}
                        i.e. {'action': 'edit_bio', 'data': 'something'}
                        i.e. {'action': 'edit_avatar', 'data': 'something'}
                        i.e. {'action': 'edit_skill_level', 'data': 'Expert', 'skill': 'skill_name'}
                        i.e. {'action': 'edit_cur_city', 'data': 'city'}
                        i.e. {'action': 'edit_cur_state', 'data': 'state'}
                        i.e. {'action': 'edit_cur_country', 'data': 'country'}
        :return: {} if successful or {"error": "some error"} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'data' not in params:
            return json.dumps({"error": "Not enough data"})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_POST']:
            return json.dumps({'error': 'Action is not allowed'})

        # Check if action is in _ACTION list
        if params['action'] not in self._ACTION['_POST']:
            return json.dumps({"error": "Action is unavailable"})

        # Getting everything we need
        table = self._ACTION['_POST'][params['action']][0]
        column = self._ACTION['_POST'][params['action']][1]

        # Apply edit
        query = "UPDATE {0} SET {1} = %s WHERE user_id = (SELECT user_id FROM users WHERE username = %s) "
        # Forming parameters for query to pass into self.cur.execute()
        query_params = (params['data'], cherrypy.session['user'], )
        # If editing skill's level
        if 'edit_skill_level' == params['action']:
            query += "AND skill = %s;"
            query_params += (params['skill'], )
        else:
            query += ";"
        # Execute the query
        self.cur.execute(query.format(table, column), query_params)
        # Apply changes to database
        self.db.connection.commit()

        return json.dumps({})

    """ PUT request handler """
    def PUT(self, **params):
        """
        Adding username and email into database

        :param params:  See _ACTION at the top of this file for list of actions
                        i.e {'action': 'add_user', 'username': 'something', 'email': 'something@email.com'}
                        or {'action': 'add_skill', 'skill': 'skill'}
        :return: {} if successful or {"error": "some error"} of failed
        """
        msg = {}        # Message to return
        # Check if there's enough data
        if ('action' not in params or 'username' not in params or 'email' not in params) and \
           ('skill' not in params):
                return json.dumps({"error": "Not enough data"})

        # Check if action is allowed
        if params['action'] not in self._ACTION['_PUT']:
            return json.dumps({'error': 'Action is not allowed'})

        # If it's adding user
        if params['action'] == 'add_user':
            # msg will be json formatted
            msg = add_new_user(self.cur, params['username'], params['email'])

        # If it's adding skill
        if params['action'] == 'add_skill' and \
           'user' in cherrypy.session:
            # msg will be JSON formatted
            msg = add_user_skill(self.cur, cherrypy.session['user'], params['skill'])

        # Apply changes to database
        self.db.connection.commit()
        return msg

    """ DELETE request handler """
    def DELETE(self, **params):
        """
        Deleting specific user's details like skills

        :param params:  See _ACTION at the top of this file for list of actions
                        i.e {'action': 'delete_skill', 'skill': 'skill'}
        :return: {} if successful or {"error": "some error"} if failed
        """
        # Check if everything is provided
        if 'action' not in params or \
           'data' not in params:
            return json.dumps({"error": "Not enough data"})

        # Check if the action is in _ACTION
        if params['action'] not in self._ACTION['_DELETE']:
            return json.dumps({"error": "Action is not allowed"})

        # Prepare everything we need
        table = self._ACTION['_DELETE'][params['action']][0]
        column = self._ACTION['_DELETE'][params['action']][1]

        # Form query to find and delete the skill based on the logged in user
        # DO NOT pass any user's input into query
        # SQL injection!
        query = """
                DELETE FROM {0}  
                WHERE user_id = (SELECT user_id FROM users WHERE username = %s)
                AND {1} = %s;

                UPDATE skills SET count = count - 1 WHERE name = %s;
                """

        # Send query to database
        self.cur.execute(query.format(table, column), (cherrypy.session['user'], params['skill'], params['skill']))

        # Apply changes to database
        self.db.connection.commit()

        return json.dumps({})

####################
# Helper functions #
####################

""" Format users' details """
def format_user_details(full=False, fetch=None):
    """
    Turning user_details into a list of dictionary

    :param full: True if for full user details
    :param fetch: the fetched database from caller
    :return: a list of user_details
    """
    user_details = []       # List of user details
    # For each user in fetch
    for user in fetch:
        dict = {}
        # When not getting full details
        dict['user_id'] = user[0]
        dict['username'] = user[1]
        dict['full_name'] = user[4]
        dict['avatar'] = user[6]
        # Format skill into a list of dictionaries
        # that have skill name and its level
        user_skills = []
        for skill, level in zip(user[7], user[8]):
           user_skills.append({'name': skill, 'level': level}) 
        dict['user_skills'] = user_skills
        # When full=True
        if full:
            dict['email'] = user[2]
            dict['join_date'] = user[3].strftime('%m-%d-%Y')
            dict['bio'] = user[5]
        # Appending the dictionary into user_details list
        user_details.append(dict)
    return user_details

""" Add user """
def add_new_user(cur=None, username=None, email=None):
    # Put username and email into our database
    # if the username isn't existed yet
    # also create a row for in user_extras and user_locs
    query = """
            DO $$
            DECLARE
                id INT;
                usr VARCHAR;
            BEGIN
                usr = %s;
                PERFORM user_id FROM users WHERE username = usr;
                IF NOT FOUND THEN
                    INSERT INTO users (username, email, join_date)
                    VALUES (usr, %s, %s) RETURNING user_id INTO id;

                    INSERT INTO user_extras (user_id)
                    VALUES (id);

                    INSERT INTO user_locs (user_id)
                    VALUES (id);
                END IF;
            END
            $$
            """
    cur.execute(query, (username, email, date.today(), ))
    # Successfully added new user
    return json.dumps({})

""" Add skill """
def add_user_skill(cur=None, user=None, skill=None):
    # Check if the skill has already been in his account
    query = """
            SELECT * FROM user_skills
            WHERE user_id = (SELECT user_id FROM users WHERE username = %s)
            AND skill = %s;
            """
    cur.execute(query, (user, skill, ))
    if cur.fetchall():
        return json.dumps({"error": "User already has that skill"})

    # Add skill into account and increase the skill's count
    query = """
            INSERT INTO user_skills (user_id, skill)
            VALUES ((SELECT user_id FROM users WHERE username = %s), %s);
            UPDATE skills SET count = count + 1 WHERE name = %s;
            """
    cur.execute(query, (user, skill, skill, ))
    # Do not commit in here, commit in UserHandler class
    return json.dumps({})
