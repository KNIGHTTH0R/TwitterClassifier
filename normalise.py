#!/usr/bin/python
# -*- coding: utf-8 -*-
    
import argparse
import re
import string
import sys

# NLTK presented "hate you." as 'hate' 'you' and "@user" as '@' 'user'
# So we wrote our own. Anyway we might be interested in emoticons..
# Some parsers may wish to preserve the following this function
# is for those who don't:
#  * Unicode emoticons such as <U+1F600> - grinning face.
#  * ASCII emoticons :( :)) etc.
#  * Quoted text.
#  * Exclamation and question marks.
#
def lose_all_punctuation( post ):
    
    # Then strip punctuation we don't want.
    exclude = r"""`!£$%^&*()_-+=//{[}]:;"~#|\<,>.?"""
    replace_punctuation = string.maketrans(exclude, ' '*len(exclude))
    no_punct = post.translate( replace_punctuation )

    # Now ' is a special case because it could be an apostrophe
    # and we must distinguish "I'll" from "ill".
    # Except we are going language dependent again.
    # We follow the word2vec way I'll -> I_ll
    # FIXME: Should convert to a clever lambda function ..
    no_single_quotes = re.sub(r"\s'|'\s|^'|'$", " ", no_punct )
    return re.sub( "'", "_", no_single_quotes ) # Convert apostrophe

def is_number( word ):
    try:
        float( word )
        return True
    except ValueError:
        return False

def is_retweet( words ):
    if words[0] == "rt":
        return True;	# Appears to be a Twitter Retweet 
    else:
        return False;

def is_rant( word ):
    if not '@' in post:
        return True;
    else:
        return False;

def normalise_post( post ):
    # Discard any obviously uninteresting posts.
    if ( ( post == None ) or ( len( post ) == 0 ) ):
        return False, None;	# Ignore empty tweets

    # May be an overkill to use NLTK, but we must separate "kill!!!" into two words.
    # NLTK presents "hate you." as 'hate' 'you' and "@user" as '@' 'user'

    lc_words = post.lower()
    
    # Anonymise @usernames.
    # FIXME: Do we filter out unicode emoticons such as <U+1F612> ?
    no_usernames = re.sub( r"@\b[A-Z,a-z,0-9_]+\b", "@person", lc_words )


    # Naively convert any htxx URL to @http 
    no_urls = re.sub( r"ht[a-z][\w-]+://\b[A-Za-z0-9./]+\b", "@http", no_usernames )

    words = lose_all_punctuation( no_urls ).lower().split()
    if len(words) == 0:
        return False, None;	# Nothing of interest remains.

    # Convert 'ggooooddd' to 'ggoodd' to optimise but still
    # distinguish from 'god'.
    # Not too happy about this as it's a language dependent hack.
    for i in range( len( words ) ):
        words[i] = re.sub(r'(.)\1+', r'\1\1', words[i])

    # FIXME:
    # a) Strip out pure digits. really what about 1, 2 and 3??
    # b) Strip out unicode ... " for example??
    # c) Do we allow '*' for stuff like h*te??

    # Return the split words.
    return True, words

###############################################################################

if __name__ == '__main__':
    print "Unit Tests ..."
    assert( normalise_post( None ) == ( False, None ) )
    assert( normalise_post( "" ) == ( False, None ) )
    assert( normalise_post( "..." ) == ( False, None ) )
    assert( normalise_post( "I'M" ) == ( True, ['i_m'] ) )
    assert( normalise_post( "All good Men." ) == ( True, ['all','good','men'] ) )
    assert( normalise_post( "ggooooddd" ) == ( True, ['ggoodd'] ) )
    assert( normalise_post( "@algebra" ) == ( True, ['@person'] ) )
    assert( normalise_post( "http://asHDADAfaf123" ) == ( True, ['@http'] ) )
    assert( normalise_post( "http://t.co/a/b/c/d/e/0/1/" ) == ( True, ['@http'] ) )
    assert( normalise_post( "http://t.co/0Melst8QEs" ) == ( True, ['@http'] ) )
    assert( normalise_post( "Hello!!! @person, Have a look at this: http://asHDADAfaf123 and this https://123agaga @a @bb :)" ) == (True, ['hello', '@person', 'have', 'a', 'look', 'at', 'this', '@http', 'and', 'this', '@http', '@person', '@person']) )

