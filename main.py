import cgi
import wsgiref.handlers
import logging
import os

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache

import gdata.photos.service
import gdata.media
import gdata.service
import gdata.alt.appengine
import atom
import atom.http_interface
import atom.token_store
import atom.url

import settings

class MainPage(webapp.RequestHandler):
  def get(self):
    html = '<div style="text-align: right;">%s</div>' % render_auth_link()
    
    if self.request.get('user_id'):
      user_id = self.request.get('user_id').encode('utf-8')
      html += render_user_id_form(user_id)
      html += render_photos(user_id)
    else:
      html += render_user_id_form('')
    
    self.response.out.write("<html><body>%s</body></html>" % html)

class UpgradeTokenPage(webapp.RequestHandler):
  def get(self):
    gd_client = get_gdata_client()

    auth_sub_token = gdata.auth.extract_auth_sub_token_from_url(self.request.uri)
    logging.info("auth_sub_token=%s" % auth_sub_token)
    
    if auth_sub_token:
      session_token = gd_client.upgrade_to_session_token(auth_sub_token)
    
    if session_token:
      memcache.add('token', session_token, 3600)
    
    self.redirect('/')

def render_auth_link():
  gd_client = get_gdata_client()
  next_url = atom.url.Url('http', settings.HOST_NAME, path='/upgrade_to_session_token')
  return '<a href="%s">Request token</a>' % gd_client.GenerateAuthSubURL(
    next_url, ('http://picasaweb.google.com/data/',), secure=False, session=True)

def get_gdata_client():
  gd_client = gdata.photos.service.PhotosService()
  gdata.alt.appengine.run_on_appengine(gd_client)
  return gd_client

def render_user_id_form(user_id):
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

  session_token = memcache.get('token')
  if session_token:
    logging.info("session_token=%s" % session_token)
    gd_client.current_token = session_token

  html = ''
  for album in gd_client.GetUserFeed(user=user_id).entry:
    html += '<div style="border: dotted 1px gray; margin: 10px; padding: 0 10px;">'
    html += '<h2>%s</h2>\n' % album.title.text
    html += '<p>\n'
    for photo in gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user_id, album.gphoto_id.text)).entry:
      html += '<img src="%s" />\n' % photo.media.thumbnail[2].url 
    html += '</p>\n</div>\n'
  return html

def main():
  application = webapp.WSGIApplication([
                                       ('/', MainPage),
                                       ('/upgrade_to_session_token', UpgradeTokenPage), 
                                       ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
