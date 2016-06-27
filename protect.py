#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import Conviction
import ngram		# Ngram classification class.
import normalise
import re
import sys
import time
import TwitterRest	# Twitter REST API access class.
import TwitterUser	# Twitter User class.

# FIXME: The various filename parameters should all go into some
#        configuration file. Same with stuff like frequencies.
#        But not verbose for example.
# FIXME: How about ngram classifiers for corporate accounts,
#        female accounts and age < 16 accounts??

if __name__ == '__main__':

   # We are running this module directly, not simply importing it.
    parser = argparse.ArgumentParser(
             description="Protect a Twitter user",
             usage=
              "usage: %(prog)s [-a] [-m] [-p] [-r] [-s] [-v]\n"
              + "                [--badcorpus=<file>]\n"
              + "                [--frequency=<float>]\n"
              + "                [--mention_limit=<int>\n"
              + "                [--neutralcorpus=<file>]\n"
              + "                [--pickle] [ --restore ]\n"
              + "                [--shoot]\n"
              + "                [--topwords=<int>]\n"
              + "                [--verbose]\n")

    parser.add_argument("-b", "--badcorpus",
                        action='store',
                        default=None,
                        dest='bad_corpus',
                        help="Corpus of abusive posts",
                        type=argparse.FileType('r'),
                        required=True)

    parser.add_argument("-f", "--frequency",
                        action="store",
                        default=0.5,
                        dest="abuse_freq",
                        type=float,
                        required=False,
                        help="Frequency of abuse probability")

    parser.add_argument("-m", "--mention_limit",
                       action="store",
                       default=10,
                       dest="mention_limit",
                       type=int,
                       required=False,
                       help="How many mentions should we study?")

    parser.add_argument("-n", "--neutralcorpus",
                       action='store',
                       default=None,
                       dest='neutral_corpus',
                       help="Corpus of neutral posts",
                       type=argparse.FileType('r'),
                       required=False)

    parser.add_argument("-p", "--pickle",
                       action='store_true',
                       default=False,
                       dest='pickle',
                       help="Persist of Corpus of neutral posts",
                       required=False)

    parser.add_argument("-r", "--restore",
                       action="store_true",
                       default=False,
                       dest="restore",
                       required=False,
                       help="Restore the pickled neutral posts to save time.")

    parser.add_argument("-s", "--shoot",
                        action="store_true",
                        default=False,
                        dest="shoot",
                        required=False,
                        help="Turn on the whole shooting match")

    parser.add_argument("-t", "--topwords",
                       action="store",
                       default=200,
                       dest="top_words",
                       type=int,
                       required=False,
                       help="Top abuse words to print in verbose mode only")

    parser.add_argument("-v", "--verbose",
                       action="count",
                       default=0,
                       dest="verbose",
                       help="Print status messages to stdout")

    args = parser.parse_args()
    if ( args.verbose > 2 ):
        print "badcorpus     = %s" % args.bad_corpus
        print "neutralcorpus = %s" % args.neutral_corpus
        print "pickling      = %s" % args.pickle
        print "restoring     = %s" % args.restore
        print "top_words     = %s" % args.top_words
        print "abuse_freq    = %s" % args.abuse_freq

    assert ( args.neutral_corpus or args.restore), \
             "Must supply either neutral corpus or a restore request"

    assert ( not ( args.neutral_corpus and args.restore) ), \
             "Neutral corpus and restore request are mutually exclusive"

    verbose = args.verbose
    shoot = args.shoot
    mention_limit = args.mention_limit

    # Construct our classifiers
    # Currently we only have language classifiers looking for potential
    # abuse posts.
    # FIXME: Extend for online grooming.
    if ( shoot ):
       print "Loading unigram training data"
       unigram = ngram.Ngram( "unigram classifier",
             args.bad_corpus, args.neutral_corpus,
             verbose, args.top_words,
             args.pickle, args.restore, 1, args.abuse_freq )

       print "Loading bigram training data"
       bigram = ngram.Ngram( "bigram classifier",
              args.bad_corpus, args.neutral_corpus,
              verbose, args.top_words,
              args.pickle, args.restore, 2, args.abuse_freq )

       print "Loading trigram training data"
       trigram = ngram.Ngram( "trigram classifier",
               args.bad_corpus, args.neutral_corpus,
               verbose, args.top_words,
               args.pickle, args.restore, 3, args.abuse_freq )
    else:
       unigram = None
       bigram  = None
       trigram = None

    ts = TwitterRest.TwitterRest( verbose )

    repeat = True;
    while repeat:
      recipient_name = raw_input('\nPlease enter username to monitor (or "." to finish):')
      if ( recipient_name == '.' ):
          repeat = False
          break

      # Get a basic profile for @person being monitored to ensure they exist.
      recipient_name = re.sub( "^@", "", recipient_name )
      found, recipient_info = ts.get_user_info( recipient_name, None )

      if not found:
        print "I cannot locate user " + recipient_name + " , please retry\n"
        continue

      # Analyse the timeline for the monitored user to get a view of their language.
      recipient = TwitterUser.TwitterUser( recipient_info, verbose, unigram, bigram, trigram )
      ufound, timeline = ts.get_user_timeline( None, recipient.get_userid(), 200 )
      if ufound:
         for idx, post in enumerate(timeline):
               hack = None
               if ( shoot ):
                  recipient.analyse( idx, post )
      else:
        print "I cannot locate user " + recipient.get_name() + " , please retry\n"
        continue
      
      recipient.pprint_basics( )

      # Now get their [historical] mentions
      print "\nScanning the last {0} posts directed at {1} ..\n".format( mention_limit, recipient.get_name() )
      mfound, mentions = ts.get_user_mentions( recipient.get_name(), mention_limit )
      if mfound:
        for idx, post in enumerate( mentions['statuses'] ):
           banter, origin = recipient.check_mention( post, shoot, mentions )

           cn = Conviction.Conviction( verbose, ts )

           # The unigram "a" post is 0.739
           # The bigram "you are" is 0.79
           # the trigram "you are" is 0.79
           if ( ( banter[1] > 0.75 ) or ( banter[2] > 0.75 ) or ( banter[3] > 0.75 ) ): 
              # We have seen some kind of ngram match.
              print( "Possible abusive post from sender {0} .. analysing account".format( origin ) ) 
      
              sfound, sender_info = ts.get_user_info( origin, None )

              if not sfound:
                print "Error: I cannot locate sender " + origin + " , please retry\n"
              else:
                sender = TwitterUser.TwitterUser( sender_info, verbose, unigram, bigram, trigram )
                
                if ( verbose > 2 ):
                   sender.basic_print()
                cn.convict( ts, sender, recipient, banter )

           else:
              print( "Post from {0} is of no interest".format( origin ) )
              cn.no_interest()

           print("Level: {0} Conviction\n".format( cn.get_conviction_str() ) )
      else:
        print( "There were no recent mentions of {0}".format( recipient.get_name() ) )

