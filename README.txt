This project is available under the GPL-3.0+ License.

Original source code by M. Hart. Uploaded to be shared with the HackHarassment Community.

Classifier and scraper of Twitter data.


***
*** NOTE: gunzip the /data/*corpus.txt.gz files before following the instructions below ***
***

Detection of social media abuse on Twitter.

1. Just load Python on your Linux dev. box and install the common python packages
   listed at the end of this doc.
   Then install the good and bad posts under data.
   Then run :
    ./protect.py -p -b=./data/bad_corpus.txt -v -n ./data/good_corpus.txt

   This will read the data and parse it and stick it into pickled (binary persistence)
   files. This can take a while which is why we pickle. (Pickle is a standard Python library).

   Then you can run again in restore from pickle mode (Note we only pickle "good" data
   as it's about 10 million lines). Pickling does use a lot of heap so if you run out
   Linux will kill protect and so just run with less good data.
   There is a protect --help and you'll notice that --shoot is needed if you want to
   do the Bayesian stuff with the good/bad corpus and deduce Twitter reputations and
   relationships in real time. All the code uses Python classes and many files have there own
   small unit tests when you run them directly.

   To recover the pickled good data and start using invoke:
   ./protect.py -r -b=./data/bad_corpus.txt --shoot

   This is a mode where we:
   a) Analyse an individual post - This use simple bayesian to come out with a value between 0 and 1.
   b) Analyse the Sender/Recipient relationship/language and activity for
      potentially abusive tweets (Remembering that good friends often call each
      other names on social media!)
      The rating system is my own home grown scale.

The project consists of a set of Python scripts and two training data files.
The good training data was harvested using harvest and the bad
manually.
Both the good and bad data corpora should be normalised using
anonymous.py. This is to change URLs to @url, Twitter names to @person, etc.

# Training data
data/bad_corpus.txt  This consists of abusive or potential abusive Tweets that I have
                     harvested from widely publicised Twitter abuse cases.
                     Plus I used harvest.py to pick up directed tweets in real time and
                     then scanned for posts that I would find offensive if I received them
                     from a stranger. 9I know a bit subjective!)
data/good_corpus.txt
                     This is about 10 million directed tweets harvested over several weeks
                     (To dampen any large political or seasiojn trends).
                     In a real world scenario you would refresh the "good" data regularly to
                     ensure the language was up to date.
                     harvest.py limited its work to geo-coded tweets from the UK.
                     
# Python scripts
anonymous.py	- Anonymises a corpus of posts (@person and @url)
bow.py          - Pretty useless bag of [tagged] words classifier.
harvest.py	- Harvests posts using Twitter Stream API
                  containing words in the set 'u,I,you,ur'
                  This is to targeted directed posts, rather than
                  informational posts.
ngram_freq.py	- Standlone tool to exercise ngram.py in isolation.
ngram.py	- Ngram classifier exploiting
parse.py	- Invokes ngram frequency classifiers on each input post
                  to compare scores. An ngram is a single word, we use
                  ngram sequences of 1 to 5 words.

TwitterUser.py    Analyse and store information about an individual Twitter user
TwitterRest.py	  Set up and use Twitter REST API connection. This uses my oauth2 certs.
                  To use your own just set up a Twitter app account and then you can get your
                  own and hack the script to use them.
rateme.py	  Rate Twitter users (using TwitterRest and TwitterUser modules)

# Data set
bad_corpus.txt	- Manual harvest of abusive tweets 
		  (normalised and anonymised).
good_corpus.txt	- Automatically harvesteid directed tweets.
		  (normalised and anonymised).

raw.txt		- Raw directed tweets
uraw.txt	- Unique raw directed tweets (mainly to remove multiple 
                  retweets).

# How to harvest a set of tweets using track words of 'I,you,u"
script /tmp/harvest.txt
./harvest.py 
dos2unix -f /tmp/harvest.txt
sort /tmp/harvest.txt | egrep -v "Rate limiting caused us to miss" | uniq >> /tmp/uniq.txt
cat /tmp/uniq.txt > ./data/raw.txt
sort ./data/raw.txt | uniq > ./data/uraw.txt

# How to anonymise a data set:
# Simply changes @name -> @user
./anonymous.py --posts=./data/uraw.txt > ./data/good_corpus.txt

# Stand alone ngram utility: Examine [1-5] word frequency and
# pickling to /tmp/pickle.[1-5]
./ngram_freq.py -g 1 -b=./data/bad_corpus.txt -n ./data/good_corpus.txt -vv -t 50 -p

# Stand alone ngram utility: Examine [1-5] word frequency and
# restore from /tmp/pickle.[1-5]
./ngram_freq.py -g 1 -b=./data/bad_corpus.txt -vv -t 50 -r

# Runs all the classifiers on some fabricated "test" data. (Pickling)
./parse.py --bow=./data/bow.txt --botw=./data/botw.txt -p -b=./data/bad_corpus.txt -vv -n ./data/good_corpus.txt -t 50

# Runs all the n-gram classifiers on some fabricated "test" data. (Use restored data).
./parse.py -r -b=./data/bad_corpus.txt

# Prerequisites
sudo apt-get install python-oauth2
sudo apt-get install python-nltk
sudo apt-get install python-sklearn
#sudo apt-get install python-reverend

=================================================================================================
Example run:

mhart@AYLDEVGTICMH02:~/work/cyber/deliver$ ./protect.py -r -b=./data/bad_corpus.txt --shoot
Loading unigram training data
   Total neutral words read:    108054618
   Total neutral unique words:  1279870
   Total abusive words read:    5168
   Total abusive unique words:  1198
Loading bigram training data
   Total neutral words read:    100621036
   Total neutral unique words:  10962617
   Total abusive words read:    4555
   Total abusive unique words:  3293
Loading trigram training data
   Total neutral words read:    93187456
   Total neutral unique words:  31135365
   Total abusive words read:    3942
   Total abusive unique words:  3611

Please enter username to monitor (or "." to finish):algebrawinter
Screen_name:  AlgebraWinter
Followers:    306
Following:    529
Verified:     False
Analysed posts:   199
Others Favoured :  0
Others retweeted:  5
Favourited :      0.50 %   ( 1 )
Retweeted  :      27.64 %   ( 55 )
Replied    :      46.23 %   ( 92 )
Contain media:    11.56 %   ( 23 )
Directed     :    76.88 %    ( 153 )
Contain URLs :    15.58 %   ( 31 )
Directed banter:  [0.979527206187] [0.977736701987] [0.0]
Retweeted banter: [0.989263326519] [0.98506147432] [0.0]
Ranting banter:   [0.9609991814] [0.983482656073] [0.0]

Scanning the last 10 posts directed at AlgebraWinter ..

Post:   I will see you later @algebrawinter (This will be flagged; in some relationship graphs this will be detected as bullying).
bigram classifier highly rated 'i will' as 0.815693254981
Possible abusive post from sender lillybet64 .. analysing account
(+80) lillybet64 has 0 followers
(+80) lillybet64 is following 0 accounts
(+25) lillybet64 has no profile URL
(+25) lillybet64 has a default profile
(+25) lillybet64 has a default profile image
Level: ( 735 ) Reasonable Conviction

Post:   Hi there @algebrawinter (This post in contrast will not be flagged by our anti cyber bullying software).
Post from lillybet64 is of no interest
(0) No interest in this post
Level: ( 0 ) No Conviction

Post:   I have said it before, I'll say it again @algebrawinter you are a total muppet.
unigram classifier highly rated 'total' as 0.994793242173
unigram classifier highly rated 'muppet' as 0.99787618911
bigram classifier highly rated 'it again' as 0.825363982835
bigram classifier highly rated '@person you' as 0.85456562678
bigram classifier highly rated 'you are' as 0.777853363228
bigram classifier highly rated 'are a' as 0.949932353891
bigram classifier highly rated 'a total' as 0.99710077598
trigram classifier highly rated '@person you are' as 0.92248010914
trigram classifier highly rated 'you are a' as 0.944775357918
trigram classifier highly rated 'are a total' as 0.998985785735
Possible abusive post from sender lillybet64 .. analysing account
(+80) lillybet64 has 0 followers
(+80) lillybet64 is following 0 accounts
(+25) lillybet64 has no profile URL
(+25) lillybet64 has a default profile
(+25) lillybet64 has a default profile image
Level: ( 735 ) Reasonable Conviction

Post:   @AlgebraWinter I can't lie - Titus was one of the best things I have ever seen.
bigram classifier highly rated 'have ever' as 0.873192751731
trigram classifier highly rated 'i have ever' as 0.903392124028
Possible abusive post from sender PrettiestTrain .. analysing account
(-240) AlgebraWinter follows PrettiestTrain
(-60) PrettiestTrain follows AlgebraWinter
(-80) PrettiestTrain has 431 followers
(-40) PrettiestTrain is following 489 accounts
Level: ( 80 ) No Conviction

Post:   @AlgebraWinter Like these algebra2? website for e-learning! http://t.co/DttgTXU4nk http://t.co/ZSgu0efmxb
Post from math_nvgt is of no interest
(0) No interest in this post
Level: ( 0 ) No Conviction

Post:   @AlgebraWinter Not seen a dragonfly yet this summer, unfortunately. Manage to be beautiful &amp; highly efficient bug-munchers...
Post from _AlexandraClare is of no interest
(0) No interest in this post
Level: ( 0 ) No Conviction

Post:   @AlgebraWinter Hey don't look at me like I have some reasonable explanation - it's Walter! #Fringe
Post from MDWobotics is of no interest
(0) No interest in this post
Level: ( 0 ) No Conviction


Please enter username to monitor (or "." to finish):.

