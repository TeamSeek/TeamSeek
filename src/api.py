import cherrypy
import json
import projects
import auth
import feed
import suggestions
import users
import skills
import applications
import notifications
import invitations

class WebRoutes(object):
    def __init__(self, db=None):
        if db:
            # mount /api/projects/ page
            # receiving GET only
            # require: go to file projects to see requirements
            self.projects = projects.ProjectHandler(db)

            # mount /api/feed/ page
            # require: cherrypy.session['user']
            self.feed = feed.ProjectFeeds(db)

            # mount /api/suggestions/ page
            # require:
            #   cherrypy.session['user']
            #   project_id
            self.suggestions = suggestions.QualifiedUsers(db)

            # mount /api/users/ page
            # require:
            #   Look into [GET], [POST], [PUT], [DELETE] methods
            self.users = users.UserHandler(db)

            # mount /api/skills/ page
            self.skills = skills.SkillHandler(db)

            # mount /api/applications/ page
            # require:
            #   Look into [GET]. [POST], [PUT], [DELETE] methods
            self.applications = applications.ApplicationHandler(db)

            # mount /api/notifications/ page
            # require:
            #   Look at [GET], [POST], [PUT], [DELETE] methods
            self.notifications = notifications.NotificationHandler(db)

            # mount /api/invitations/ page
            # require:
            #   Look at [GET], [POST], [PUT], [DELETE] methods
            self.invitations = invitations.InvitationHandler(db)

            # mount /api/auth/ page
            # maps /api/auth/github and /api/auth/debug
            self.auth = auth.WebRoutes(db)
        else:
            print "api.py >> Error: Invalid database connection"

    """ Accessed from "/api/example/" """
    @cherrypy.expose
    def example(self, **params):
        result = {'working': 'yup'}
        # json.dumps takes a python dict and produces a JSON string
        return json.dumps(result)
