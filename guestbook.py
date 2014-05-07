import cgi
import urllib
import webapp2

from google.appengine.api import users
from google.appengine.ext import ndb

# https://developers.google.com/appengine/docs/python/gettingstartedpython27/handlingforms

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
        self.response.write( '<html><body> ' )
        guestbook_name = self.request.get( 'guestbook_name', 
                                           DEFAULT_GUESTBOOK_NAME )

        # so Greeting just "acquire" properties by taking ndb.Model ?
        #
        greetings_query = Greeting.query( 
            ancestor = guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        for greeting in greetings:
            if greeting.author:
                self.response.wite( 
                    '<b>%s</b> wrote:' % greeting.author.nickname())
            else:
                self.response.write( 'An anonymous user wrote:' )
            self.response.write('<blockquote>%s</blockquote>' %
                                cgi.escape( greeting.content))

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        # write the submission form and the footer of the page
        sign_query_params = urllib.urlencode({'guestbook_name' : guestbook_name})
        self.response.write( MAIN_PAGE_FOOTER_TEMPLATE % (sign_query_params, 
                                                          cgi.escape(guestbook_name),
                                                          url, url_linktext))
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

#        self.response.write('<!doctype html><html><pre>')
#        self.response.write(cgi.escape(self.request.get('content')))
#        self.response.write('</pre></body></html>')

# this variable name "app" must match what is stated in yaml file
app = webapp2.WSGIApplication( [
    ('/', Mainpage),
    ('/sign', Guestbook),
], debug=True)
