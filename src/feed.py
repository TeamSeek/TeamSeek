""" This file handles anything related to feeds
    be it algorithm or feed suggestions.

    Accessed from /api/feed/
"""

import cherrypy
import json
import projects


class ProjectFeeds(object):

    """ This handles getting database connection """
    def __init__(self, db=None):
        if db:
            self.db = db
            self.cur = db.connection.cursor()
        else:
            print "feed.py >>  Error: Invalid database connection"

    """ This handles forwarding HTTP request methods """
    @cherrypy.expose
    def index(self):
        # Checking if user is logged in
        # Don't let anyone trying something fishy
        if 'user' not in cherrypy.session:
            return json.dumps({"error": "You shouldn't be here"})

        # Forwarding HTTP request
        http_method = getattr(self, cherrypy.request.method)
        return http_method()

    """ Handling GET method """
    @cherrypy.tools.accept(media='text/plain')
    def GET(self):
        """
        :return: JSON format of projects
        """
        query = """
                SELECT	project_info.project_id, title, owner, short_desc, last_edit, posted_date,
                        (SELECT update FROM project_extras WHERE project_id=project_info.project_id),
                        (SELECT git_link FROM project_extras WHERE project_id=project_info.project_id),
                        array(SELECT skill FROM project_skills WHERE project_id=project_info.project_id),
                        array(SELECT member FROM project_members WHERE project_id=project_info.project_id)
                FROM    project_info
                WHERE   project_id = ANY (SELECT project_id FROM project_skills WHERE skill =ANY
                                            (SELECT skill FROM user_skills WHERE user_id =
                                                (SELECT user_id FROM users WHERE username = %s)));
                """
        self.cur.execute(query, (cherrypy.session['user'], ))
        fetch = self.cur.fetchall()

        if not fetch:
            query = """
                    SELECT	project_id, title, owner, short_desc, last_edit, posted_date,
                            (SELECT update FROM project_extras WHERE project_id=project_info.project_id),
                            (SELECT git_link FROM project_extras WHERE project_id=project_info.project_id),
                            array(SELECT skill FROM project_skills WHERE project_id=project_info.project_id),
                            array(SELECT member FROM project_members WHERE project_id=project_info.project_id)
                    FROM    project_info;
                    """
            self.cur.execute(query)
            fetch = self.cur.fetchall()

        # Reusing helper function from projects
        project_details = projects.format_project_details(False, self.cur, fetch)

        return json.dumps(project_details[:10], indent=4)

    """ Handling POST method """
    def POST(self):
        return json.dumps({"error": "POST request is not supported"})

    """ Handling PUT method """
    def PUT(self):
        return json.dumps({"error": "PUT request is not supported"})

    """ Handling DELETE method """
    def DELETE(self):
        return json.dumps({"error": "DELETE request is not supported"})
