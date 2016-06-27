#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import normalise
import re
import sys
import time

class TwitterUser:
   def __init__( self, user_info_json, verbose, unigram, bigram, trigram ):
      self.verbose = verbose
      self.screen_name = user_info_json.get('screen_name').encode('utf-8')
      self.name        = user_info_json.get('name').encode('utf-8')
      # FIXME: Do we want the string version of and) id??
      self.twitter_id  = user_info_json.get('id')
      self.protected   = user_info_json.get('protected')

      self.followers   = user_info_json.get('followers_count')
      self.following   = user_info_json.get('friends_count')
      self.lists       = user_info_json.get('listed_count')
      self.favourited  = user_info_json.get('favourites_count')
      self.posts       = user_info_json.get('statuses_count')
      self.created     = user_info_json.get('created_at')
      self.own_url     = user_info_json.get('url')

      self.verified    = user_info_json.get('verified')
      self.geo_enabled = user_info_json.get('geo_enabled')
      self.language    = user_info_json.get('lang')

      self.description = user_info_json.get('description')
      self.url         = user_info_json.get('url')

      self.default_profile = user_info_json.get('default_profile')
      self.default_profile_image = user_info_json.get('default_profile_image')

      # The following is not so useful. It's pretty optional.
      self.utc         = user_info_json.get('utc_offset')
      self.timezone    = user_info_json.get('time_zone')

      self.stats = {}
      self.stats['i_favorited']       = 0
      self.stats['i_retweeted']       = 0
      self.stats['in_reply']          = 0
      self.stats['others_favorited']  = 0
      self.stats['others_retweeted']  = 0
      self.stats['contains_media']    = 0
      self.stats['contains_mentions'] = 0
      self.stats['contains_urls']     = 0
      self.stats['total']             = 0
  
      # Classifiers for abuse rating
      self.unigram = unigram
      self.bigram = bigram
      self.trigram = trigram

      # Banter statistics. ( [1] = unigram. [2] = bigram. [3] = trigram )
      self.directed_banter = [0.0, 0.0, 0.0, 0.0]
      self.retweeted_banter = [0.0, 0.0, 0.0, 0.0]
      self.ranting_banter = [0.0, 0.0, 0.0, 0.0]

   def basic_print( self ):
      verified = "unverified"
      if ( self.get_verified() == True ):
          verified = "verified"

      protected = "unprotected"
      if ( self.get_protected() == True ):
          protected = "protected"

      print( "User {0} has {1} followers, follows {2} and is {3},{4}".format(
              self.get_name(),
              self.get_followers(),
              self.get_following(),
              verified,
              protected
            ) )

   def pprint_basics( self ):

      print "Screen_name: ", self.screen_name 
      print "Followers:   ", self.followers
      print "Following:   ", self.following
      print "Verified:    ", self.verified

      if self.verbose > 1:
        print "Id:          ", self.twitter_id
        print "Name:        ", self.name 
        print "Lists:       ", self.lists
        print "Favourited:  ", self.favourited
        print "Posts:       ", self.posts
        print "Created:     ", self.created
        print "URL:         ", self.own_url

        print "Protected:   ", self.protected
        print "Geo Enabled: ", self.geo_enabled

        print "Description: ", self.description
        print "URL:         ", self.url

        print "Def. profile:", self.default_profile
        print "Def. image:  ", self.default_profile_image

      # The following is not so useful. It's pretty optional.
      if self.verbose > 2:
          print "UTC:         ", self.utc
          print "Timezone:    ", self.timezone
          print "Language:    ", self.language

      posts = self.stats['total']
      if posts > 0:
        print "Analysed posts:  ", posts
        posts = posts / 100.0
        print"Others Favoured : ", self.stats['others_favorited']
        print"Others retweeted: ", self.stats['others_retweeted']
        print"Favourited :      %.2f" % (self.stats['i_favorited']/ posts),"%   (", self.stats['i_favorited'], ")"
        print"Retweeted  :      %.2f"% (self.stats['i_retweeted'] / posts),"%   (", self.stats['i_retweeted'], ")"
        print"Replied    :      %.2f"% (self.stats['in_reply'] / posts),"%   (", self.stats['in_reply'], ")"
        print"Contain media:    %.2f"% (self.stats['contains_media'] / posts),"%   (", self.stats['contains_media'], ")"
        print"Directed     :    %.2f"% (self.stats['contains_mentions'] /posts),"%    (", self.stats['contains_mentions'], ")"
        print"Contain URLs :    %.2f"% (self.stats['contains_urls'] / posts),"%   (", self.stats['contains_urls'], ")"

        print( "Directed banter:  [{0}] [{1}] [{2}] ".format(
               self.directed_banter[1],
               self.directed_banter[2],
               self.directed_banter[3]
              ) )

        print( "Retweeted banter: [{0}] [{1}] [{2}] ".format(
               self.retweeted_banter[1],
               self.retweeted_banter[2],
               self.retweeted_banter[3]
              ) )

        print( "Ranting banter:   [{0}] [{1}] [{2}] ".format(
               self.ranting_banter[1],
               self.ranting_banter[2],
               self.ranting_banter[3]
              ) )
      else:
         print "***No posts have been analysed, so stats are not available.**"

   def get_userid( self ):
       return self.twitter_id

   def get_name( self ):
       return self.screen_name

   # These are useful accessors for determining abusive users.
   def get_description( self ):
      return self.description

   def get_url( self ):
      return self.url

   def is_default_profile( self ):
      return self.default_profile

   def is_default_profile_image( self ):
      return self.default_profile_image

   def get_created( self ):
       return self.created

   def get_verified( self ):
       return self.verified

   def get_protected( self ):
       return self.protected

   def get_followers( self ):
       return self.followers

   def get_following( self ):
       return self.following

   def sends_directed_banter( self ):
       if ( self.directed_banter[1] > 0.0 ):
          return True

       return False

   def check_mention( self, post, shoot, rate_verbose ):

      sender = post['user']['screen_name']
      post_text = post['text'].encode('ascii', 'ignore')

      if ( self.verbose or rate_verbose ):
          print( "Post:   {0} ".format(post['text'].encode('utf-8') ) )
      if self.verbose > 2:
          print( "Sender: {0} ".format(sender) )

      banter_rating = [0.0, 0.0, 0.0, 0.0]

      if ( ( post['retweet_count'] > 0) and 
           ( 'retweeted_status' in post.keys() ) and
           ( post['retweeted_status']['user']['id'] == self.twitter_id ) ):
         print( "This post is a pure retweet of {0} .. ignoring".format ( self.screen_name ) )
         of_interest = False
      else:
         of_interest, words = normalise.normalise_post( post_text )

      if of_interest:
          for i in range( len( words ) ):
              if ( self.verbose > 2 ): 
                  print i , words[i]

          for ng in range (1,4):
              # There is no switch in python..
              if ng == 1:
                  ngram = self.unigram
              elif ng == 2:
                  ngram = self.bigram
              else:
                  ngram = self.trigram

              # Harvest the maximum rating.
              if ( shoot ):
                rate_verbose = True	# Always on for mentions..
                alert, rating = ngram.rate( words, rate_verbose )
              else:
                rating = 1.0  # HACK

              banter_rating[ng] = rating;

      if self.verbose:
          print( "Banter ratings: {0}".format( banter_rating[1:4] ) )
      return banter_rating, sender

   def analyse( self, idx, post):
       if self.verbose > 1:
           print "    " + str(idx) + "          " + post['text'].encode('utf-8')
      
       # Harvest basic statistics
       self.stats['total'] += 1
       if post['favorited']:
           self.stats['i_favorited'] += 1

       # Is this post an original?
       if 'retweeted_status' in post:
           self.stats['i_retweeted'] += 1
       else:
           # An original tweet, now these interest us the most.
           if 'retweet_count' in post:
               self.stats['others_retweeted'] += post['retweet_count']

           if 'favorite-count' in post:
               self.stats['others_favourited'] += post['favorite-count']

       # Is this post a reply?
       if 'in_reply_to_status_id' in post and post['in_reply_to_status_id']:
           self.stats['in_reply'] += 1

       if len( post['entities']['urls'] ):
           self.stats['contains_urls'] += 1

       if len( post['entities']['user_mentions'] ):
           self.stats['contains_mentions'] += 1

       if ( 'media' in post['entities']):
           self.stats['contains_media'] += 1

       # Now parse this post using a number of raters.
       post_text = post['text'].encode('ascii', 'ignore')
       of_interest, words = normalise.normalise_post( post_text )

       if not of_interest:
           if self.verbose:
               print "No interest in this post"
       else:
           rate_verbose = False
           if ( self.verbose > 2 ):
               rate_verbose = True
               for i in range( len( words ) ):
                   print i , words[i]

           for ng in range (1,3):
	     # There is no switch in python..
             if ng == 1:
               ngram = self.unigram
             elif ng == 2:
               ngram = self.bigram
             else:
               ngram = self.trigram

             if ( ngram ):
               alert, rating = ngram.rate( words, rate_verbose )
             else:
               alert, rating = False, 0.0

             # Save the highest ratings we find. 
             # FIXME: Do we also save the mean, median, standard distribution?
             if 'retweeted_status' in post:
               if rating > self.retweeted_banter[ng]:
                 if ( self.verbose > 1 ):
                   print "Retweeted banter: " , self.retweeted_banter[ng] , " -> " , rating
                 self.retweeted_banter[ng] = rating;

             elif len( post['entities']['user_mentions'] ):
               if rating > self.directed_banter[ng]:
                 if ( self.verbose > 1 ):
                   print "Directed banter: " , self.directed_banter[ng] , " -> " , rating
                 self.directed_banter[ng] = rating;

             else:
               if rating > self.ranting_banter[ng]:
                 if ( self.verbose > 1 ):
                   print "Ranting banter: " , self.ranting_banter[ng] , " -> " , rating
                 self.ranting_banter[ng] = rating;

if __name__ == '__main__':
    print "Unit Tests ..."
    verbose = 2
    user_info_json = json.loads('{"screen_name": "Ellie", "name": "Ellie Smith"}')
    unigram = None
    bigram = None
    trigram = None
    user = TwitterUser ( user_info_json, verbose, unigram, bigram, trigram )
    post = { "text": "Hello world!!!!", "favorited": 1, "entities": { "urls": {}, "user_mentions": {} } }
    user.analyse( 1, post )
    user.pprint_basics()

