#!/usr/bin/python
    
import argparse
import normalise
import re
import string
import sys

###############################################################################
class SimpleBagOfWords:
    def __init__(self, name, bow, verbose):
    # Class instantiation.
    # Using http://en.wikipedia.org/wiki/List_of_ethnic_slurs
    # and  http://en.wikipedia.org/wiki/List_of_LGBT_slang
    # similar to http://www.floatingsheep.org for geography of hatecrime maps.
        self.name = name
        self.verbose = verbose
        badwords = []
        for line in bow:
            if ( not '#' in line ) and ( not ':' in line) :
                lc_line = line.lower()
                words = lc_line.split()
                for i in range( len( words ) ):
                    words[i] = re.sub(r'(.)\1+', r'\1\1', words[i])
                    badwords.append( words[i] )
                    # No longer needed -> badwords.append( '#' + words[i] )
        
        # FIXME: Do we need to worry about repeated instances??
        self.bagofwords = set( badwords )

    def getName( self ):
        return self.name

    def rate( self, words ):
        for i in range( len( words ) ):
            if words[i] in self.bagofwords:
               if self.verbose:
                  print "--->", words[i]
               return True, None
        return False, None

###############################################################################
def get_tag( line ):
    tags = line.split(':')
    return tags[0]
    
class BagOfTaggedWords:
    def __init__(self, name, botw, verbose):
        # Class instantiation.
        self.verbose = verbose
        self.name = name
        tag = None
        self.tags = dict()	# Use a dictionary because we may have classes of tags.
        self.badwords = dict()	# FIXME: Slower than {} ??
        for line in botw:
            if ':' in line:
                # Tag encountered.
                tag = get_tag( line )
                self.tags[tag] = True
            else:
                if ( not '#' in line ):
                    assert tag, "No tag has been specified"
                    lc_line = line.lower()
                    words = lc_line.split()
                    for i in range( len( words ) ):
                        words[i] = re.sub(r'(.)\1+', r'\1\1', words[i])
                        if words[i] in self.badwords.keys():
                            assert 0, "Duplicate word in botw: " + words[i]
                        self.badwords[ words[i] ] = tag
        if self.verbose > 1:
            print "Words:"
            print self.badwords
            print len( self.badwords )
            print "Tags:"
            print self.tags
            print len( self.tags )

    def getName( self ):
        return self.name

    def rate( self, words ):
        rating = dict()
        result = False
        for i in range( len( words ) ):
            word = words[i]
            if word in self.badwords:
                tag = self.badwords[ word ]
                if tag in rating.keys():
                   rating[tag] += 1 
                else:
                   rating[tag] = 1

        if len( rating):
            result = True

        return result, rating

###############################################################################

