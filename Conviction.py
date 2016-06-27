#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import time
import datetime

class Conviction:
  def __init__( self, verbose, ts ):
    self.conviction = 500	# Midpoint 0..1000
    self.verbose = verbose
    self.ts = ts
    self.months = {
         'Jan': '01', 'Feb': '02', 'Mar' : '03', 'Apr' : '04',
         'May': '05', 'Jun': '06', 'Jul' : '07', 'Aug' : '08',
         'Sep': '09', 'Oct': '10', 'Nov' : '11', 'Dec' : '12'
    }

  def is_recent_date( self, past_date ):
    # Return < 1 month, < 1 week, < 1 day

    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(1)
    last_week = today - datetime.timedelta(7)
    last_month = today - datetime.timedelta(30)

    now_str  = today.strftime('%Y-%m-%d')
    yesterday_str  = yesterday.strftime('%Y-%m-%d')
    last_week_str  = last_week.strftime('%Y-%m-%d')
    last_month_str  = last_month.strftime('%Y-%m-%d')

    if ( self.verbose > 2 ):
      print past_date
    month = past_date[4:7]
    day =  past_date[8:10]
    year = past_date[26:30]
    past = year + "-" + self.months[month] + "-" + day 

    # Default to old accounts..
    since_yday = False
    since_last_week = False
    since_last_month = False

    if ( self.verbose > 2 ):
      print "Yesterday: " + yesterday_str
      print "last week: " + last_week_str
      print "last mont: " + last_month_str
      print "Past:      " + past

    if ( past > yesterday_str ):
       since_yday = True

    if ( past > last_week_str ):
       since_last_week = True

    if ( past > last_month_str ):
       since_last_month = True

    return ( since_yday, since_last_week, since_last_month )

  def reduce_conviction( self, level = 1 ):
    if ( self.conviction > level):
      self.conviction -= level
    else:
      self.conviction = 0

  def increase_conviction( self, level = 1 ):
    # We never upgrade a "no interest" post.
    if ( self.conviction > 0 ):
      self.conviction += level

  def no_interest( self ):
    self.conviction = 0
    print "(0) No interest in this post"

  def get_conviction_str( self ):
    if ( self.conviction <= 300 ):
      convicted = "No"
    elif ( self.conviction <= 500 ):
      convicted = "Very weak"
    elif ( self.conviction <= 600):
      convicted = "Weak"
    elif ( self.conviction <= 700):
      convicted = "Some"
    elif ( self.conviction <= 800 ):
      convicted = "Reasonable"
    elif ( self.conviction <= 900 ):
      convicted = "Strong"
    else:
      convicted = "Overwhelming"

    return "( " + str(self.conviction) + " ) " + convicted

  def convict( self, ts, sender, recipient, banter ):
    # FIXME: We need empirical evidence and probabilities for these
    #        convictions, not just my "good" ideas.

    sender_id = sender.get_userid()
    recipient_id = recipient.get_userid()

    sender_name = sender.get_name()
    recipient_name = recipient.get_name()

    if ( self.verbose > 2 ):
       print( "{0} --sent to--> {1}\n".format( sender_id, recipient_id ) )

    # Special cases.
    if ( sender_id == recipient_id ):
       # User is simply mentioning themselves..
       self.no_interest()
    else:
       sender_follows, recipient_follows = ts.get_friendships( sender_name, recipient_name )
       if ( recipient_follows ):
             print("(-240) {0} follows {1}".format( recipient_name, sender_name ) )
             self.reduce_conviction( 240 )

       if ( sender_follows ):
             print("(-60) {0} follows {1}".format( sender_name, recipient_name ) )
             self.reduce_conviction( 60 )

    # Conditions that mean an abusive post is less likely..
    if ( sender.get_verified() ):
      print( "(-200) {0} is a verified account".format( sender_name ) )
      self.reduce_conviction( 200 )

    move = ""
    # Conditions that mean an abusive post is less likely..
    if ( sender.get_followers()  > 10000 ):
      self.reduce_conviction( 150 )
      move = "(-150)"
    elif ( sender.get_followers()  > 2000 ):
      self.reduce_conviction( 140 )
      move = "(-140)"
    elif ( sender.get_followers()  > 1000 ):
      self.reduce_conviction( 120 )
      move = "(-120)"
    elif ( sender.get_followers()  > 500 ):
      self.reduce_conviction( 100 )
      move = "(-100)"
    elif ( sender.get_followers()  > 250 ):
      self.reduce_conviction( 80 )
      move = "(-80)"
    elif ( sender.get_followers()  > 100 ):
      self.reduce_conviction( 60 )
      move = "(-60)"
    elif ( sender.get_followers()  > 40 ):
      self.reduce_conviction( 40 )
      move = "(-40)"
    elif ( sender.get_followers()  > 20 ):
      self.reduce_conviction( 20 )
      move = "(-20)"
    # Conditions that mean an abusive post is more likely..
    elif ( sender.get_followers() < 1 ):
      self.increase_conviction( 80 )
      move = "(+80)"
    elif ( sender.get_followers() < 4 ):
      self.increase_conviction( 40 )
      move = "(+40)"
    elif ( sender.get_followers() < 8 ):
      self.increase_conviction( 20 )
      move = "(+20)"
    elif ( sender.get_followers() < 16 ):
      self.increase_conviction( 10 )
      move = "(+10)"
    print( move + " {0} has {1} followers".format( sender_name, sender.get_followers() ) )

    move = ""
    if ( sender.get_following()  > 1000 ):
      self.reduce_conviction( 60 )
      move = "(-60)"
    elif ( sender.get_following()  > 500 ):
      self.reduce_conviction( 50 )
      move = "(-50)"
    elif ( sender.get_following()  > 250 ):
      self.reduce_conviction( 40 )
      move = "(-40)"
    elif ( sender.get_following()  > 100 ):
      self.reduce_conviction( 30 )
      move = "(-30)"
    elif ( sender.get_following()  > 40 ):
      self.reduce_conviction( 20 )
      move = "(-20)"
    elif ( sender.get_following()  > 20 ):
      self.reduce_conviction( 10 )
      move = "(-10)"
    # Conditions that mean an abusive post is more likely..
    elif ( sender.get_following() < 1 ):
      self.increase_conviction( 80 )
      move = "(+80)"
    elif ( sender.get_following() < 4 ):
      self.increase_conviction( 40 )
      move = "(+40)"
    elif ( sender.get_following() < 8 ):
      move = "(+20)"
      self.increase_conviction( 20 )
    elif ( sender.get_following() < 16 ):
      self.increase_conviction( 10 )
      move = "(+10)"
    print( move + " {0} is following {1} accounts".format( sender_name, sender.get_following() ) )

    if ( sender.get_protected() ):
      print( "(+20) {0} is a protected account".format( sender_name ) )
      self.increase_conviction( 20 )
      
    created = str(sender.get_created() )
    since_yday, since_last_week, since_last_month = self.is_recent_date( created )
    if ( since_yday ):
         print "(+500) {0} was created on {1} - in the last 2 days".format( sender_name, created )
         self.increase_conviction( 500 )
    elif ( since_last_week ):
       if ( self.verbose ):   
         print "(+200) {0} was created on {1} - in the last 7 days".format( sender_name, created )
         self.increase_conviction( 200 )
    elif ( since_last_month ):
         print "(+100) {0} was created {1} - in the last 30 days".format( sender_name, created )
         self.increase_conviction( 100 )

    # Look for recipients who have little interaction ..
    if ( recipient.sends_directed_banter() == False ):
       if ( self.verbose ):   
         print( "(+100) {0} has sent no directed posts recently". format( recipient_name ) )
         self.increase_conviction( 100 )

    # FIXME: Now convict based on the strength of the banter ..

    # FIXME - Also convict for:
    # a) Sender is an egg pic
    # b) sender has no profile URL
    # c) sender has no profile text.
    if ( sender.get_description() == None ):
       print("(+50) {0} has no profile description".format( sender_name ) )
       self.increase_conviction( 50 )

    if ( sender.get_url() == None ):
       print("(+25) {0} has no profile URL".format( sender_name ) )
       self.increase_conviction( 25 )

    if ( sender.is_default_profile() ):
       print("(+25) {0} has a default profile".format( sender_name ) )
       self.increase_conviction( 25 )

    if ( sender.is_default_profile_image() ):
       print("(+25) {0} has a default profile image".format( sender_name ) )
       self.increase_conviction( 25 )


if __name__ == '__main__':
    print "Unit Tests ..."
    cn = Conviction( 1, None )
    #print( cn.get_conviction_str() )
    assert( cn.get_conviction_str() == "( 500 ) Very weak" )

    cn.no_interest()
    assert( cn.get_conviction_str() == "( 0 ) No" )

    assert( cn.is_recent_date( "Wed Jun 20 15:11:06 +0000 2012" ) == (False, False, False ) )
    assert( cn.is_recent_date( "Wed May 20 15:11:06 +0000 2013" ) == (False, False, False ) )
    assert( cn.is_recent_date( "Wed Dec 20 15:11:06 +0000 2015" ) == (True, True, True ) )
    assert( cn.is_recent_date( "Wed Mar 19 15:11:06 +0000 2014" ) == (False, True, True ) )
    assert( cn.is_recent_date( "Wed Mar 02 15:11:06 +0000 2014" ) == (False, False, True ) )


