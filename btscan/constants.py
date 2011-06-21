"""
A bunch of configuration constants.

"""


LOGDIR = "/tmp"





PID_PATH = "/tmp"





#
# Constants for Name Lookup
#

# I'll probably want to drop these down for 
# valid devices
# though 6 seconds isn't really that bad

BT_TIMEOUT = int(7)

# how many secs between successful name updates for people with names?

NAME_UPDATE_THRESHOLD = 60*30 # once every 30 minutes if we have a name for their device

# how often to check device names that failed last time
NAME_UPDATE_FAILED_LAST_TIME = 2  # once every 10 secs, check those that failed

NAME_UPDATE_FAILED_MAX = 15 # once they have failed 5 times, only check every 30 minutes
NAME_UPDATE_FAILED_MAX_TIME = 60*60 # only check those that have failed 5 times, once every hour

HIDDEN_UPDATE_THRESHOLD = 20 # only check the same device once every 30 seconds

# I don't even know if I am going to do this.
# Based on the memory ussage of some of my older ruby scripts,
# I may want to have something to expire old items in the cache.
CACHE_CLEAR_TIME = 24*60*60

# poll for clearing cache items every 4 hours
CACHE_CLEAR_POLL = 60*60*4  



#
# Constants for NEAR/FAR Management
#
DEBUG = 0

NEAR_EXPIRE = 50
FAR_EXPIRE  = 70

NEAR_THRESHOLD = 70 
NEAR_LEAVE_THRESHOLD = 72

UPDATE_THRESHOLD = 30
NEAR_PROB = 0.8
FAR_PROB  = 0.3

NORMAL_EXPIRE = 90
HIDDEN_EXPIRE = 60 * 10

# how often do I remove cache entries (once an hour)
CLEANUP_TIME = 60 * 60
EXPIRE_FREQ = 10


#
# just for fun
#

class Filter:
  pass