#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import bow              # Bag of [Tagged] Words classifer
import re
import sys
import time
import TwitterRest
import TwitterUser

if __name__ == '__main__':

   # We are running this module directly, not simply importing it.
   parser = argparse.ArgumentParser(
            description="Rate a Twitter user",
            usage=
              "usage: %(prog)s [-v] [-i]\n"
            + "                [--botw=<file>]\n"
            )

   parser.add_argument("-i", "--ids",
                      action="store_true",
                      default=False,
                      dest="ids",
                      required=False,
                      help="Rate based on userids")

   parser.add_argument("-B", "--botw",
                      action='store',
                      dest='botw',
                      help="Bag of tagged words",
                      type=argparse.FileType('r'),
                      required=True)

   parser.add_argument("-v", "--verbose",
                      action="count",
                      default=0,
                      dest="verbose",
                      required=False,
                      help="Print status messages to stdout")
   args = parser.parse_args()

   if ( args.botw ):
       botw = bow.BagOfTaggedWords( "Tag Bag", args.botw, args.verbose )
   else:
       botw = None
 
   ts = TwitterRest.TwitterRest( args.verbose )
   repeat = True
   if args.ids:
       prompt = 'Please enter a user id (or "." to finish):'
       not_found = 'User id not found\n'
   else:
       prompt = 'Please enter a user name (or "." to finish):'
       not_found = 'User not found\n'

   while repeat:
      user_handle = raw_input( prompt)
      if (user_handle == '.'):
         repeat = False
      else:
         # Strip out any leading '@'
         if args.ids:
             found, user_info_json = ts.get_user_info( None, user_handle )
         else:
             user_handle = re.sub( "^@", "", user_handle )
             found, user_info_json = ts.get_user_info( user_handle, None )

         if found:
             user = TwitterUser.TwitterUser( user_info_json, args.verbose, botw )
             found, timeline = ts.get_user_timeline( None, user.get_userid(), 200 )
             if found:
                 for idx, post in enumerate(timeline):
                     user.analyse( idx, post )
             else:
                 print "   Timeline not accessible"
             user.pprint_basics()
         else:
             print not_found

