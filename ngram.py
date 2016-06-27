#!/usr/bin/python
import collections
import math
import nltk
import normalise
import pickle
import re
import string
import sys

#------------------------------------------------------------------------------
# ngram.py (multiple adjacent word) classifier
#
# Under the hood uses NLTK.ngrams and NLTK.FreqDist plus Pickle.
#
# An ngram can consist of between 1 and 5 words.
# So for example "I like toast" -> ngram(1) = "I", "like", "toast"
#                "I like toast" -> ngram(2) = "I like", "like toast"
#
# Training data:
# a) A corpus of manually harvested abusive tweets
# b) A large corpus of harvested directed tweets over a one month.
#
# score( post ) = max( score(individual ngrams) )
# score( word ) =                 frequency(word,abuse).freq(abuse)
#                  ------------------------------------------------------------
#                  frequency(word, abuse).freq(abuse) + freq(word,neutral).freq(neutral)
#
# We *could* use collections.Counter() if we solve the 
# 'not pickle-able as it's an instance method.' issue. That might be faster!
#
# For ngrams we lose all punctuation, numbers and emoticons, we can ease
# this if we see a need; perhaps pure numbers are unlikely in abuse.
# Also we do not handle '@person She said to me "You muppet"' for example.
#------------------------------------------------------------------------------

def termFreq( word_sequence, freq ):
    return ( float(freq[ word_sequence ]) / float( freq.N() ) )

class Ngram:

    PICKLE_BASE = "/tmp/pickle."

    def printStats( self ):
        print "   Total neutral words read:   ", self.neutral_freq.N()
        print "   Total neutral unique words: ", self.neutral_freq.B()
        if ( self.verbose > 2 ):
          print( "   Top neutral top words:      ",
            self.neutral_freq.tabulate( self.top_words ) )

        print "   Total abusive words read:   ", self.abuse_freq.N()
        print "   Total abusive unique words: ", self.abuse_freq.B()
        if ( self.verbose > 2 ):
          print( "   Top abusive words:          ",
             self.abuse_freq.tabulate( self.top_words ) )

          assert( sum( self.abuse_freq.values() ) == self.abuse_freq.N() )
          assert( sum( self.neutral_freq.values() ) == self.neutral_freq.N() )

    def frequency( self, corpus_file ):

        # use nltk.ngrams( line, self.ngrams )
        freq = nltk.FreqDist()
        for line in corpus_file:
            if ( not (line[0] == '#' and line[1] == ' ') ):
                of_interest, normalised_line = normalise.normalise_post( line )
 
                if of_interest:
                    ngrams_group = nltk.ngrams(normalised_line, self.ngrams)
                    for ngram in ngrams_group:
                        unit = " ".join( ngram )
                        freq.inc( unit, 1 )
                else:
                    if self.verbose > 3:
                        s = "Discarded line from corpus: ", line
                        print s
        
        # Ensure we are at the start of file.
        corpus_file.seek(0, 0)
        return freq

    def __init__( self, name, bad_corpus, neutral_corpus, verbose,
                  top_words, pickle, restore, ngrams, abuse_probability ):

        assert ( abuse_probability > 0.0 ) and ( abuse_probability < 1.0 ), "Abuse frequency out of range"
        assert ngrams in range(1,5) , "Ngrams must be in range 1..5"

        self.name = name
        self.ngrams = ngrams
        self.verbose = verbose
        self.abuse_probability   = float( abuse_probability );
        self.neutral_probability = float( 1 - abuse_probability );

        pickle_filename = self.PICKLE_BASE + str(ngrams)

        if restore:
            assert not pickle, "Restore and pickle are mutually exclusive"
            restore_file = open( pickle_filename, 'r' )
            assert restore_file, "Cannot read " + restore_filename
            self.neutral_freq = self.restore( restore_file )
        else:
            self.neutral_freq  = self.frequency( neutral_corpus )

        self.abuse_freq   = self.frequency( bad_corpus ) 
        self.top_words = top_words

        self.printStats()
    
        if pickle:
            pickle_file = open( pickle_filename, 'w' )
            assert pickle_file, "Cannot open for write " + pickle_filename
            self.pickle( pickle_file )

    def getName( self ):
        return self.name

    # Persist only the neutral tweets as they form the large corpus
    def pickle( self , pickle_file ):
        pickle.dump( self.neutral_freq.copy(), pickle_file )

    def restore( self , pickle_file ):
        return pickle.load( pickle_file )

    def rate( self, words, rate_verbose = False ):
        top_score = 0.0
        is_abusive = False
        ngrams_group = nltk.ngrams( words, self.ngrams)
        for ngram in ngrams_group:
            word_sequence = " ".join( ngram )
            abuse_tf   = termFreq( word_sequence, self.abuse_freq )
            neutral_tf = termFreq( word_sequence, self.neutral_freq )
            abuse_score   = abuse_tf * self.abuse_probability
            neutral_score = neutral_tf * self.neutral_probability
            if ( abuse_score + neutral_score ) > 0.0 :
                ngram_score = abuse_score / ( abuse_score + neutral_score )
                if ( ngram_score > top_score ):
                    top_score = ngram_score
            else:
                ngram_score = 0.0
                
            if ( rate_verbose  ):
              if ngram_score > 0.75:
                print("{0} highly rated '{1}' as {2}".format(
                   self.name, word_sequence, ngram_score
                ) )

        if ( top_score > 0.75 ):
            # FIXME: How arbitrary is that??
            is_abusive = True
 
        if ( self.verbose > 2) :
            print( "Final score: {0} {1}".format( top_score, is_abusive ) )
        
        return is_abusive, top_score

