import cgi
import wsgiref.handlers
import logging
import os
from google.appengine.ext.webapp import template

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache

import gdata.photos.service
import gdata.media
import gdata.geo
import gdata.service
import gdata.alt.appengine
import atom
import atom.http_interface
import atom.token_store
import atom.url

import settings

class MainPage(webapp.RequestHandler):
  def get(self):

    client = gdata.photos.service.PhotosService()
    gdata.alt.appengine.run_on_appengine(client)
    
    if users.get_current_user():

      if memcache.get(users.get_current_user().email()) is not None:
        client.token_store.add_token(memcache.get('token'))
      else:
        
        auth_token = gdata.auth.extract_auth_sub_token_from_url(self.request.uri)
        session_token = None
        if auth_token:
          session_token = client.upgrade_to_session_token(auth_token)
          memcache.add(users.get_current_user().email(), session_token, 3600)

        if session_token and users.get_current_user():
          client.token_store.add_token(session_token)
        elif session_token:
          client.current_token = session_token
      
      if users.get_current_user() != '':
        albums = []
        html = '<html>'
        for album in client.GetUserFeed(user=users.get_current_user()).entry:
          html += '<h2>%s</h2>' % album.title.text
          html += '<p style="padding: 0 10xp;">'
          photos = client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (users.get_current_user(), album.gphoto_id.text))

          for photo in photos.entry:
            html += '<img src="%s" />' % photo.media.thumbnail[2].url 

          html += '</p>'

        template_values = {
          'albums': albums,
          }

        self.response.out.write(html)
      else:
        self.response.out.write('not login')

class TestPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(users.get_current_user().email())

class AuthPage(webapp.RequestHandler):
  def get(self):
    client = gdata.photos.service.PhotosService()
    gdata.alt.appengine.run_on_appengine(client)
    next_url = atom.url.Url('http', settings.HOST_NAME, path='/photos')
    self.response.out.write("""<html><body>
        <a href="%s">Request token for the Picasa Scope</a>
        </body></html>""" % client.GenerateAuthSubURL(next_url,
            ('http://picasaweb.google.com/data/',), secure=False, session=True))

# /photos
class PhotosPage(webapp.RequestHandler):
  def get(self):
    user_id = self.request.get('user_id')
    
    html = render_user_id_form(user_id)

    if user_id:
      html += render_photos(user_id)

    self.response.out.write("<html><body>%s</body></html>" % html)

def get_gdata_client():
  gd_client = gdata.photos.service.PhotosService()
  gdata.alt.appengine.run_on_appengine(gd_client)
  return gd_client

def render_user_id_form(user_id):
  if user_id is None:
    user_id = ''
  form_html = """
<form method="get">
<div>User ID:</div>
<input type="text" name="user_id" value="%s" />
<input type="submit" value="Show" />
</form>
"""
  return form_html % user_id

def render_photos(user_id):
  gd_client = get_gdata_client()

  html = ''

  for album in gd_client.GetUserFeed(user_id).entry:
    html += '<h2>%s</h2>\n' % album.title.text
    html += '<p>\n'

    for photo in gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user_id, album.gphoto_id.text)).entry:
      html += '<img src="%s" />\n' % photo.media.thumbnail[2].url 

    html += '</p>\n'

  return html

def main():
  application = webapp.WSGIApplication([
                                       ('/', MainPage),
                                       ('/photos', PhotosPage), 
                                       ('/login', LoginPage), 
                                       ('/auth', AuthPage),
                                       ('/test', TestPage)
                                       ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
