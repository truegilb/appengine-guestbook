import cgi
import os
import urllib
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb
import jinja2

# https://developers.google.com/appengine/docs/python/gettingstartedpython27/handlingforms

JINJA_ENVIRONMENT=jinja2.Environment(
 loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
 extensions=['jinja2.ext.autoescape'],
 autoescape=True
)

MAIN_PAGE_HTML = """\
<!doctype html>
<html>
  <body>
    <form action="/sign" method="post">
      <div><textarea name="content" rows="3" cols="60"></textarea></div>
      <div><input type ="submit" value="Sign Guestbook"></textarea></div>
    </form>
  </body>
</html>
"""

MAIN_PAGE_FOOTER_TEMPLATE="""\
  <form action="/sign?%s" method="post">
    <div><textarea name="content" rows="3" cols="60"></textarea></div>
    <div><input type="submit" value="Sign guestbook"></div>
  </form>
  <hr>
  <form>Guestbook name:
    <input value="%s" name="guestbook_name"></input>
    <input type="submit" value="switch"></input>
  </form>
  <a href="%s">%s</a>
  </body>
</html>  
"""

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

def guestbook_key( guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """ Contructs a datastore key for a guestbook """
    return ndb.Key( 'Guestbook', guestbook_name )

# greeting is a subclass of ndb.Model
class Greeting( ndb.Model ):
    author = ndb.UserProperty()
    content = ndb.StringProperty( indexed=False)
    date = ndb.DateTimeProperty( auto_now_add= True)

class Mainpage( webapp2.RequestHandler):
    def get(self):
        guestbook_name = self.request.get( 'guestbook_name', 
                                           DEFAULT_GUESTBOOK_NAME )

        # so Greeting just "acquire" properties by taking ndb.Model ?
        #
        greetings_query = Greeting.query( 
            ancestor = guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'greetings' : greetings,
            'guestbook_name' : urllib.quote_plus(guestbook_name),
            'url' : url,
            'url_linktext' : url_linktext,
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render( template_values))

class Guestbook( webapp2.RequestHandler):
    def post(self):
        guestbook_name = self.request.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))
        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get( 'content')
        greeting.put()
        query_params = { 'guestbook_name' : guestbook_name }
        self.redirect( '/?' + urllib.urlencode( query_params))

class ClearGuestbook( webapp2.RequestHandler):
    def post(self):
        guestbook_name = self.request.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query( 
            ancestor = guestbook_key(guestbook_name))
        greetings = greetings_query.fetch()

        # grab all the rows (entities in NDB speak) and purge one-by-one
        for greeting in greetings:
          greeting.key.delete()

        query_params = { 'guestbook_name' : guestbook_name }
        self.redirect( '/?' + urllib.urlencode( query_params))

# this variable name "app" must match what is stated in yaml file
app = webapp2.WSGIApplication( [
    ('/', Mainpage),
    ('/sign', Guestbook),
    ('/clear', ClearGuestbook)
], debug=True)
