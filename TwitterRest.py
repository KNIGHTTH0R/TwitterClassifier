#!/usr/bin/python
# -*- coding: utf-8 -*-

import cStringIO
import json
import oauth2 as oauth
import pprint
import pycurl
import re
import sys
import time
import urllib

USER_AGENT = 'TheKidsAreSafe 0.0'

# Documentation: https://dev.twitter.com/docs/api/1.1
# Note we are using OAuth 1.0A
# Applications make signed HTTP requests to Twitter in a user context.
# Typically an application obtains access tokens in order to act on behalf of a
# user account.
# Mine are https://dev.twitter.com/apps/5271247 and 5306097.
# Note if we see HTTP 401 errors, see https://dev.twitter.com/discussions/1403
#
OAUTH_KEYS = {
   # Authenticates the Consumer (or Application).
   'consumer_key':        'e5qqtSVpTT81FSUHrTVLg',
   'consumer_secret':     '1AokeUeFifdZq7Gz7Y9yyXlDGMlXYx2x4tzgaAMJ9I',

   # Authenticates the user token.
   'access_token_key':    '613514515-6lYbnHqO0o06uhxyoTGb0o8IfoZcfUfcfUxql8WB',
   'access_token_secret': 'slBLsinF0vjs5MxgZk8jiFje46YvF2oZPTPsojHJZeUwZ'
}

class TwitterRest:
   def __init__( self, verbose ):

      # FIXME: This needs to be a proper cache with time-to-live.
      #        We need it for performance so we don't re-request followers
      #        for a 'known' user and also to avoid the Twitter rating limit
      #        which freezes our account for 15 minutes.
      self.followers_list = {}

      self.verbose = verbose
      # Set up our Token instance, using keys provided by Twitter.
      access_token_key = OAUTH_KEYS['access_token_key']
      access_token_secret = OAUTH_KEYS['access_token_secret']
      self.token = oauth.Token(access_token_key, access_token_secret)

      # Set up our Consumer instance, using keys provided by Twitter.
      self.consumer_key           = OAUTH_KEYS['consumer_key']
      self.consumer_secret        = OAUTH_KEYS['consumer_secret']
      self.consumer = oauth.Consumer( self.consumer_key, self.consumer_secret)
      # These are required to authorise our twitter HTTP requests.
      # See https://dev.twitter.com/docs/auth/authorizing-request
      if self.verbose > 2:
         print self.token
         print "consumer_key: "    + self.consumer_key
         print "consumer_secret: " + self.consumer_secret
         print self.consumer

      self.conn = None

   def get_oauth_header( self, url ):
      """ Create and return OAuth header.  """
      params = {'oauth_version': '1.0',
                # A nonce is used to uniquely identify a request.
                'oauth_nonce': oauth.generate_nonce(),
                'oauth_timestamp': int(time.time())}
      req = oauth.Request(method='GET', parameters=params,
                          url='%s' % (url))
      # Sign the HTTP request with both the application and user private keys.
      req.sign_request(oauth.SignatureMethod_HMAC_SHA1(),
                       self.consumer, self.token)
      return req.to_header()['Authorization'].encode('utf-8')

   def rest_call( self, url ):
      # Twitter REST API call.
      if self.conn:
          self.conn.close()
          self.buff = ''

      buffer = cStringIO.StringIO()
      self.conn = pycurl.Curl()
 
      # Curl really doesn't like unicode .. URL must be a python string. 
      url = url.encode('ascii','ignore')
      if ( self.verbose > 2 ):
        print( "Url: {0} type:{1}".format(url, type(url)) )
      self.conn.setopt(pycurl.URL, url)
      self.conn.setopt(pycurl.USERAGENT, USER_AGENT)
      self.conn.setopt(pycurl.HTTPHEADER, 
                       ['Host: api.twitter.com',
                       'Authorization: %s' % self.get_oauth_header( url ) ] )
      self.conn.setopt(pycurl.WRITEFUNCTION, buffer.write)
      try:
         self.conn.perform()
      except:
         print >> sys.stderr,'Network error: %s' % self.conn.errstr()

      http_code = self.conn.getinfo(pycurl.HTTP_CODE)
      if self.verbose > 2:
          print "HTTP code: " + str( http_code )
          print "Response: " + buffer.getvalue()

      user_info_json = json.loads( buffer.getvalue() )
      if http_code != 200:
          if self.verbose > 2:
              pp = pprint.PrettyPrinter( indent=4 )
              pp.pprint( user_info_json )
          return False, None
      else:
          buffer.close()
          return True, user_info_json

   def get_user_info( self, screen_name, userid ):
      # Twitter REST API GET users/show supplying a screen_name or userid
      USERS_SHOW_URL = 'https://api.twitter.com/1.1/users/show.json'
      if screen_name:
          url = USERS_SHOW_URL + "?screen_name=" + screen_name
      else:
          url = USERS_SHOW_URL + "?user_id=" + str(userid)
      return self.rest_call( url )	# Returning a tuple.

   def get_followers( self, screen_name, count = 1600, cursor = -1 ):
      # Twitter REST API GET followers/ids for screen_name
      # Returns a collection of user IDs for every user following the specified user.
      # WARNING: it is very easy to hit "Rate limit exceeded"
      #          then we hit the twitter 15 minute reset period...
      # FIXME: Maybe we need to cache followers.

      ids = []
      if ( screen_name in self.followers_list ):
         ids = self.followers_list[ screen_name ]
         if ( self.verbose > 2 ):
             print( "Using cached {0} followers for {1}".format(
               len( ids['ids'] ),
               screen_name
             ))
         found = True
      else:
         FOLLOWERS_URL = 'https://api.twitter.com/1.1/followers/ids.json'
         url = FOLLOWERS_URL + "?include_entities=false"
         url = url + "&cursor=" + str(cursor)  # First page.
         url = url + "&count=" + str(count)
         url = url + "&screen_name=" + screen_name
         found, ids = self.rest_call( url )
         if ( found == True ):
           self.followers_list[ screen_name ] = ids
           if ( self.verbose > 2 ):
             print( "Adding {0} followers for {1}".format(
               len(ids['ids']),
               screen_name
             ))
           if ( ids['next_cursor'] != 0 ):
              print("Warning: You have only captured {0} ids!!".format( count )) 
         else:
           print("Warning: You have not captured followers for {0} .. Twitter rate limit??".format(
                   screen_name
           ))
      return found, ids

   def get_friendships( self, source_name, target_name ):
      FRIENDSHIP_URL="https://api.twitter.com/1.1/friendships/show.json"
      url = FRIENDSHIP_URL
      url = url + "?source_screen_name=" + source_name
      url = url + "&target_screen_name=" + target_name

      found, relationship = self.rest_call( url )       # Returning a tuple.
      if found:
         target_follows = relationship['relationship']['target']['following'] 
         source_follows = relationship['relationship']['target']['followed_by']
      else:
         target_follows = False
         source_follows = False
         print( "Warning: You have not captured the {0} {1} relationship".format(
               source_name, target_name ) )

      return source_follows, target_follows

   def get_user_mentions( self, screen_name, count = 200, since_id = 1 ):
      # Twitter REST API GET user mentions for screen_name
      # Trim out garbage like the entities node.
      USER_MENTIONS_URL = 'https://api.twitter.com/1.1/search/tweets.json'
      url = USER_MENTIONS_URL + "?include_entities=false&count=" + str(count)
      url = url + "&q=%40" + screen_name
      if since_id > 1:
           url = url + "&since_id=" + str(since_id) 
      return self.rest_call( url )	 # Returning a tuple.

   def get_user_timeline( self, screen_name, userid, count = 10 ):
      # Twitter REST API GET statuses/user_timeline supplying a screen_name or userid
      # trim out any garbage we can.
      TIMELINE_URL = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
      url = TIMELINE_URL + "?trim_user=1&count=" + str(count)
      if screen_name:
          url = url + "&screen_name=" + screen_name
      else:
          url = url + "&user_id=" + str(userid)
      return self.rest_call( url )	 # Returning a tuple.

if __name__ == '__main__':
    print "Unit Tests ..."
    verbose = 3
    ts = TwitterRest( verbose )

    #print ts.get_friendships( "AlgebraWinter", "CharlotteJW" )
    #print ts.get_friendships( "AlgebraWinter", "FatHeadfilms" )

    #found, user_info = ts.get_user_info ( 'millie', None )
    #print found, user_info
    #assert( found == True )

    #found, user_info = ts.get_user_info ( 'miles', None )
    #print found, user_info
    #assert( found == True )

    #found, user_info = ts.get_user_info ( 'the', None )
    #print found, user_info
    #assert( found == True )

    #found, user_info = ts.get_user_info ( 'milly', None )
    #print found, user_info
    #assert( found == True )

    #found, followers = ts.get_followers( 'AlgebraWinter' )
    #print followers['ids']
    #assert( found == True )

    #found, followers = ts.get_followers( 'millie' )
    #print followers['ids']
    #assert( found == True )

    #found, followers = ts.get_followers( 'miles' )
    #if ( found == False ):
       # Miles is protected!!
    #   print("They won't let us access miles .. ")
    #else:
    #   print followers['ids']

    #found, followers = ts.get_followers( 'the' )
    #print followers['ids']
    #assert( found == True )

    #found, followers = ts.get_followers( 'milly' )
    #print followers['ids']
    #assert( found == True )

    #found, followers = ts.get_followers( 'AlgebraWinter' )
    #print followers['ids']
    #assert( found == True )

    #found, followers = ts.get_followers( 'millie' )
    #print followers['ids']
    #assert( found == True )

    #found, followers = ts.get_followers( 'miles' )
    #if ( found == False ):
       # Miles is protected!!
    #   print("They won't let us access miles .. ")
    #else:
    #   print followers['ids']

    #found, followers = ts.get_followers( 'the' )
    #print followers['ids']
    #assert( found == True )

    #found, followers = ts.get_followers( 'milly' )
    #print followers['ids']
    #assert( found == True )

    #found, user_info = ts.get_user_info ( 'algebrawinter', None )
    #print found, user_info
    #assert( found == True )

    #found, user_info = ts.get_user_timeline( None, 613514515, 200 )
    #print found, user_info
    #assert( found == True )

    found, mentions = ts.get_user_mentions( 'algebrawinter', 1 )
    print found, mentions
    assert( found == True )

    #found, user_info = ts.get_user_info ( 'adam', None )
    #print found, user_info
    #assert( found == True )

    #found, user_info = ts.get_user_info( None, 17 )
    #print found, user_info
    #assert( found == True )

    #found, user_info = ts.get_user_timeline( 'algebrawinter', None, 1 )
    #print found, user_info
    #assert( found == True )

    #found, mentions = ts.get_user_mentions( 'AlgebraWinter', 100, 1 )
    #print found, mentions
    #assert( found == True )

