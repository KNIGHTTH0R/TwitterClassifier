#!/usr/bin/python
# Anonymise a stream of tweets.
# Give a stream of tweets convert first @userhandle to @person
# In addition we anonymise the obfuscated URL links.

import argparse
import re
import string
import sys

if __name__ == '__main__':
    # We are running this module directly, not simply importing it.
    parser = argparse.ArgumentParser(
         description="Anonymise posts.",
         usage="usage: %(prog)s [options] [--posts=<file>]" )

    parser.add_argument("-p", "--posts",
                      action='store',
                      default=sys.stdin,
                      dest='posts',
                      help="Input posts to anonymise",
                      type=argparse.FileType('r'),
                      required=False)
    args = parser.parse_args()

    count = 0
    for line in args.posts:
        # FIXME: Do we filter out unicode emoticons such as <U+1F612> ?
        line = re.sub(r"@\b[A-Z,a-z,0-9_]+\b", "@person", line)
        # Naively convert any htxx URL to @http 
        line = re.sub(r"ht[a-z][\w-]+://\b[A-Za-z1-9./]+\b", "@http", line )
        sys.stdout.write( line )
