#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Gustav Arngården

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
    
import json
import oauth2 as oauth
import pycurl
import re
import sys
import time
import urllib

# FIXME:
# a) The track words need to come from a larger set.
#    Maybe look for I and you with regex
#    and then word2vec rather than a bag of bad words like hate.
# b) We do seem to open a lot of connections.
# c) Check the backing off algorithm

TWITTER_FEED_URL = 'https://stream.twitter.com/1.1/statuses/filter.json'
USER_AGENT = 'TheKidsAreSafe 0.0' 

# Note we are using OAuth 1.0A
# Applications make signed HTTP requests to Twitter in a user context.
# Typically an application obtains access tokens in order to act on behalf of a
# user account.
# Mine are https://dev.twitter.com/apps/5271247 and 5306097.
# Note if we see HTTP 401 errors, see https://dev.twitter.com/discussions/1403
#
OAUTH_KEYS = {'consumer_key':        'e5qqtSVpTT81FSUHrTVLg',	# Authenticates the Consumer (or Application).
              'consumer_secret':     '1AokeUeFifdZq7Gz7Y9yyXlDGMlXYx2x4tzgaAMJ9I',
              'access_token_key':    '613514515-6lYbnHqO0o06uhxyoTGb0o8IfoZcfUfcfUxql8WB',	# Authenticates the user.
              'access_token_secret': 'slBLsinF0vjs5MxgZk8jiFje46YvF2oZPTPsojHJZeUwZ'}

# Twitter Streaming API request parameters.
# Other parameters of interest are:
# location: -180,-90,180,90 (whole globe) for only geo-tagged tweets.
# track: To track particular phrases. (Acts as a union with location).
# follow: Does NOT include mentions (except for retweets from this user).

# Note: "The Search API uses fuzzy matching and is not limited to geotagged
#       tweets. It will often try to derive a user's location from their
#       self-declared location field on their profile.
#       Some times if you were searching for Paris, France you would get
#       tweets near Paris, Texas as well. This is by design."
#       @episod, twitter platform team.

# To get geocode I used:
# http://maps.googleapis.com/maps/api/geocode/json?address=uk&sensor=false
#
STREAM_API_PARAMETERS = {
               #'delimited': 'length',  # Status are length preceded.
               'include_entities': 0,	# No entities are returned
               'language': 'en',	# English language data only
               'stall_warning': 'true',	# Periodic warnings received.
               'track': 'I,you,YOU,i,ur,u,your,youre,we,our'}

class TwitterStream:
    def __init__(self, timeout=False):	# class instantiation.

        # Set up our Token instance, using keys provided by Twitter.
        access_token_key = OAUTH_KEYS['access_token_key']
        access_token_secret = OAUTH_KEYS['access_token_secret']
        self.token = oauth.Token(access_token_key, access_token_secret)

        # Set up our Consumer instance, using keys provided by Twitter.
        consumer_key           = OAUTH_KEYS['consumer_key']
        consumer_secret        = OAUTH_KEYS['consumer_secret']
        self.consumer = oauth.Consumer(consumer_key, consumer_secret)
        # These are required to authorise our twitter HTTP requests. See https://dev.twitter.com/docs/auth/authorizing-request

        self.conn = None
        self.buffer = ''
        self.timeout = timeout
        #self.setup_connection()

    def setup_connection(self):
        """ Create persistent HTTP connection to Streaming API endpoint using cURL.
"""
        if self.conn:
            self.conn.close()
            self.buffer = ''
        self.conn = pycurl.Curl()
        # Restart connection if less than 1 byte/s is received during "timeout" seconds
        if isinstance(self.timeout, int):
            self.conn.setopt(pycurl.LOW_SPEED_LIMIT, 1)
            self.conn.setopt(pycurl.LOW_SPEED_TIME, self.timeout)
        self.conn.setopt(pycurl.URL, TWITTER_FEED_URL)
        self.conn.setopt(pycurl.USERAGENT, USER_AGENT)
        # Using gzip is optional but saves us bandwidth.
        self.conn.setopt(pycurl.ENCODING, 'deflate, gzip')
        self.conn.setopt(pycurl.POST, 1)
        self.conn.setopt(pycurl.POSTFIELDS, urllib.urlencode(STREAM_API_PARAMETERS))
        self.conn.setopt(pycurl.HTTPHEADER, ['Host: stream.twitter.com',
                                             'Authorization: %s' % self.get_oauth_header()])
        # self.handle_tweet is the method that are called when new tweets arrive
        self.conn.setopt(pycurl.WRITEFUNCTION, self.handle_tweet)

    def get_oauth_header(self):
        """ Create and return OAuth header.
"""
        params = {'oauth_version': '1.0',
                  'oauth_nonce': oauth.generate_nonce(), # A nonce is used to uniquely identify a request.
                  'oauth_timestamp': int(time.time())}
        req = oauth.Request(method='POST', parameters=params, url='%s?%s' % (TWITTER_FEED_URL,
                                                                             urllib.urlencode(STREAM_API_PARAMETERS)))
        # Sign the HTTP request with both the application and user private keys.
        req.sign_request(oauth.SignatureMethod_HMAC_SHA1(), self.consumer, self.token)
        return req.to_header()['Authorization'].encode('utf-8')

    def start(self):
        """ Start listening to Streaming endpoint.
Handle exceptions according to Twitter's recommendations.
"""
        backoff_network_error = 0.25
        backoff_http_error = 5
        backoff_rate_limit = 60
        while True:
            self.setup_connection()
            try:
                self.conn.perform()
            except:
                # Network error, use linear back off up to 16 seconds
                print >> sys.stderr,'Network error: %s' % self.conn.errstr()
                print >> sys.stderr, 'Waiting %ss before retry' % backoff_network_error
                time.sleep(backoff_network_error)
                backoff_network_error = min(backoff_network_error + 1, 16)
                continue
            # HTTP Error
            sc = self.conn.getinfo(pycurl.HTTP_CODE)
            if sc == 420:
                # Rate limit, use exponential back off starting with 1 minute and double each attempt
                print 'Rate limit, waiting %s seconds' % backoff_rate_limit
                print >> sys.stderr, 'Rate limit, waiting %ss' % backoff_rate_limit
                time.sleep(backoff_rate_limit)
                backoff_rate_limit *= 2
            else:
                # HTTP error, use exponential back off up to 320 seconds
                print >> sys.stderr, 'HTTP error %s, %s' % (sc, self.conn.errstr())
                print >> sys.stderr, 'Waiting %s seconds' % backoff_http_error
                time.sleep(backoff_http_error)
                backoff_http_error = min(backoff_http_error * 2, 320)

    def handle_tweet(self, data):
        """ This is the callback method when matching tweets arrive.
"""
        self.buffer += data
        if data.endswith('\r\n') and self.buffer.strip():
            # complete message received
            if len(self.buffer) == 0:
                print >> sys.stderr, "Empty self.buffer"
            message = json.loads(self.buffer)
            self.buffer = ''
            msg = ''
            if message.get('limit'):
                print 'Rate limiting caused us to miss %s tweets' % (message['limit'].get('track'))
            elif message.get('disconnect'):
                raise Exception('Got disconnect: %s' % message['disconnect'].get('reason'))
            elif message.get('warning'):
                print >> sys.stderr,'Warning: %s' % message['warning'].get('message')
            else:
                text = message.get('text')
                if '@' in text:
                    line = text.replace('\n', ' ')  # Retain post as one line
                    print( line )

if __name__ == '__main__':
    # We are running this module directly, not simply importing it.
    ts = TwitterStream()
    ts.setup_connection()
    ts.start()

