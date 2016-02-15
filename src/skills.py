""" This file contains any functions that relate to
    skills such as pulling skills from database, adding new skills,
    skill approval, or skill disapproval

    Accessed from /api/skills/
"""

import cherrypy
import json

class SkillHandler(object):
    """ Accessed from /skills/?q= """
    def __init__(self, db=None):
        """ Initializing object """
        # If a database connection is passed
        if db:
            self.db = db
            self.cur = db.connection.cursor()
        else:
            print "skills.py >> Error: Invalid database connection"

    """ Handling HTTP requests """
    @cherrypy.expose
    def index(self, **params):
        """ Catches the HTTP request method and forwards it to request handlers """
        # Catching HTTP request
        http_method = getattr(self, cherrypy.request.method)
        # Forward it to request handlers (below)
        return (http_method)(**params)

    ####################
    # Request handlers #
    ####################

    """ [GET] request handler """
    @cherrypy.tools.accept(media='text/plain')
    def GET(self, **params):
        """
        This handles GET requests

        :param q: the query of the skill search
        :return: json formatted of skills
        """
        # Check if everything is provided
        if 'q' not in params:
            return json.dumps({"error": "Not enough data"})

        # Execute the SQL query to get 5 skills
        # started with the entered 'q' string
        # with the most frequently used
        query = """
            SELECT name
            FROM skills
            WHERE name LIKE %s
            ORDER BY count DESC
            LIMIT 5;
        """
        self.cur.execute(query, (params['q'] + "%",))          # Prevent SQL injection
        # Fetch the result returned by database
        skills = [skill[0] for skill in self.cur.fetchall()]
        # Return the formatted of skills and used_counts
        return json.dumps(skills)

    """ [POST] request handler """
    def POST(self, **params):
        """
        Changing status (approval) of skills

        :param params: i.e. {'skill': "some-skill', 'approved': 'True'}
        :return: {} if successful. {"error": "Some error"} if failed
        """
        # Make sure you're authorized
        if not 'admin' == cherrypy.session['user']:
            return json.dumps({"error": "You're not authorized"})

        # Check if everything is provided
        if 'approved' not in params or \
           'skill' not in params:
            return json.dumps({"error": "Not enough data"})

        # Query for database
        query = "UPDATE skills SET approved = %s WHERE name = %s"
        self.cur.execute(query, (params['approved'], params['skill'], ))
        # Apply changes to database
        self.db.connection.commit()
        return json.dumps({})

    """ [PUT] request handler """
    def PUT(self, **params):
        """
        Adding new skill into database

        :param params: i.e. {'skill': 'some-skill'}
        :return : {} if successful. {'error': 'Some error'} if failed
        """
        # Make sure you're authorized
        if not 'admin' == cherrypy.session['user']:
            return json.dumps({"error": "You're not authorized"})

        # Check if everything is provided
        if 'skill' not in params:
            return json.dumps({'error': 'Not enough data'})

        # Add skill, also check if skill has already been added before
        query = """
                DO $$
                BEGIN
                    PERFORM * FROM skills WHERE name = %s;
                    IF NOT FOUND THEN
                        INSERT INTO skills (name, approved, count)
                        VALUES (%s, %s, %s);
                    END IF;
                END
                $$
                """
        self.cur.execute(query, (params['skill'], params['skill'], False, '1'))
        # Apply changes to database
        self.db.connection.commit()
        return json.dumps({})

    """ [DELETE] request handler """
    def DELETE(self, **params):
        """
        Deleting skill from database

        :param params: i.e {'skill': 'some-skill'}
        :return : {} if successful. {'error': 'some error'} if failed
        """
        # Make sure you're authorized
        if not 'admin' == cherrypy.session['user']:
            return json.dumps({"error": "You're not authorized"})

        # Check if everything is provided
        if 'skill' not in params:
            return json.dumps({"error": "Not enough data"})

        # Delete skill off database
        query = "DELETE FROM skills WHERE name = %s;"
        self.cur.execute(query, (params['skill'], ))
        # Apply changes to database
        self.db.connection.commit()
        return json.dumps({})
