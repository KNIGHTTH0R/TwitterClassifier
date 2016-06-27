#!/usr/bin/python
    
import argparse
import bow		# Bag of Words classifer
import ngram		# Ngram classifier
import normalise
import re
import string
import sys

###############################################################################
def rate_jrip( text ):
    # rules based, repeated incremental pruning.
    return True

def rate_j48( text ):
    # Decision tree based classifier.
    return True

def rate_svm( text ):
    # Support vector machine based classifier
    return True

def rate_scikits_learn( text ):
    # A simple bag of words based on hash.
    return True

def rate_word2vec( text ):
    return True

if __name__ == '__main__':
    # We are running this module directly, not simply importing it.
    parser = argparse.ArgumentParser(
         description="Evaluate posts.",
         usage=
             "usage: %(prog)s [-v] [-p] [-r]\n"
           + "                --bow=<file> --botw=<file>\n"
           + "                [--posts=<file>]\n"
           + "                [--badcorpus=<file>]\n"
           + "                [--neutralcorpus=<file>]\n"
           + "                [--pickle] [ --restore ]\n"
           + "                [--topwords=<int>]\n"
           + "                [--frequency=<float>]\n"
           + "                [--out=<file>] [--help]" )

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

    parser.add_argument("-n", "--neutralcorpus",
                      action='store',
                      default=None,
                      dest='neutral_corpus',
                      help="Corpus of neutral posts",
                      type=argparse.FileType('r'),
                      required=False)

    parser.add_argument("-o", "--out",
                      action='store',
                      default=sys.stdout,
                      dest='out',
                      help="Output of high-lighted posts",
                      type=argparse.FileType('w'),
                      required=False)

    parser.add_argument("-P", "--posts",
                      action='store',
                      default=sys.stdin,
                      dest='posts',
                      help="Input posts to evaluate",
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

    parser.add_argument("-t", "--topwords",
                      action="store",
                      default=20,
                      dest="top_words",
                      type=int,
                      required=False,
                      help="Top words to print in verbose mode")

    parser.add_argument("-v", "--verbose",
                      action="count",
                      default=0,
                      dest="verbose",
                      help="Print status messages to stdout")

    parser.add_argument("-w", "--bow",
                      action='store',
                      dest='bow',
                      help="Bag of untagged words",
                      type=argparse.FileType('r'),
                      required=False)

    parser.add_argument("-W", "--botw",
                      action='store',
                      dest='botw',
                      help="Bag of tagged words",
                      type=argparse.FileType('r'),
                      required=False)

    args = parser.parse_args()
    if ( args.verbose ):
        print "bow           = %s" % args.bow
        print "botw          = %s" % args.botw
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

    # Construct our classifiers
    if ( args.bow ):
        bagofwords = bow.SimpleBagOfWords( "BagOfWords", args.bow ) 

    if ( args.botw ):
        bagoftaggedwords = bow.BagOfTaggedWords( "TaggedBagOfWord", args.botw,
                           args.verbose )

    if ( args.verbose ):
        print "Loading unigram training data"
    unigram = ngram.Ngram( "Unigram", args.bad_corpus, args.neutral_corpus,
                           args.verbose, args.top_words,
                           args.pickle, args.restore, 1, args.abuse_freq )

    if ( args.verbose ):
        print "Loading bigram training data"
    bigram = ngram.Ngram( "Bigram", args.bad_corpus, args.neutral_corpus,
                           args.verbose, args.top_words,
                           args.pickle, args.restore, 2, args.abuse_freq )

    if ( args.verbose ):
        print "Loading trigram training data"
    trigram = ngram.Ngram( "Trigram", args.bad_corpus, args.neutral_corpus,
                           args.verbose, args.top_words,
                           args.pickle, args.restore, 3, args.abuse_freq )

    raters = [ unigram, bigram, trigram ]
    if ( args.bow):
        raters.append( bagofwords )

    if ( args.botw):
        raters.append( bagoftaggedwords )

    #for post in args.posts:
    repeat = True
    while repeat:
        post = raw_input('\nPlease enter a post including @person (or "end"):')
        if ( post == 'end' ):
            repeat = False
        else:
            of_interest, words = normalise.normalise_post( post )
            if ( args.verbose):
                print words

            if of_interest:
                for rater in raters:
                     print "\n"
                     alert, rating = rater.rate( words )
                     msg = rater.getName()
                     if alert:
                        msg += " alerts: "
                     else:
                        msg += " ignore: "
                     msg += str( rating )
                     args.out.write( msg )
 
