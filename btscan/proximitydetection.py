#
# Very simple aggregator.. all it does is
# manage expiration for the 3 types of BT packets
# 
#  
#
#  NEED TO MAKE A THREADSAFE DICTIONARY and this is good to go

import sys
import copy
import os

import random


import time
import threading
import logging
import popen2
import copy
import string

from constants import *

logger = logging.getLogger("ProximityDetection")

    
# This filter has a few purposes.
# 
class FilterAddExpiration(Filter):
  def __init__(self, normal_expire = NORMAL_EXPIRE, hidden_expire = HIDDEN_EXPIRE):
      self.normal_expire = normal_expire
      self.hidden_expire = hidden_expire
  
  def filter(self,data):
    # if it's a timer induced expiration message
    # then don't filter it
    if( data.get("isexpire_message")):
      return data
    
    if(data.get("is_hidden", False)):
      # is hidden, handle expiration in this fashion.
      data["expire"] = data.get("timestamp", time.time()) + self.hidden_expire
    
    # might want to add a case, for devices that are normally hidden.
    # either to check for it, in a filter, or.. yea... that seems best        
    else:
      data["expire"] = data.get("timestamp", time.time()) + self.normal_expire
      # normal should work fine.
      # just set the expiration generically 
      # timestamp + some multiplier

    return data # end it



class FilterSetProximity(Filter):
  def __init__(self, core, cache = {},):
    # some sort of thread safe hash
    self.cache = cache
    self.stopme = False
    self.core = core
    self.cache_lock = threading.Lock()
    # end this
   
  def determine_near(self, data):
     return (- (data.get("rssi", -999)) <= NEAR_THRESHOLD or 
              (self.cache[self.get_key( data) ]['type'] == "NEAR" and - (data.get("rssi", -999)) <= NEAR_LEAVE_THRESHOLD ) )
  
  def get_key(self,data):
    return '|'.join( [ data['addr'], str( data['x']) , str( data['y']), str(data['z']) ])
     
  # simple lock solution:
  def get_lock(self,key, data):
    lock = None
    try:
      self.cache_lock.acquire()
      if(not self.cache.get(key,False) ):
        if(DEBUG > 0):
          logger.debug("New Item in Cache %s : %s -- %s" % ( data.get('addr',False), self.cache.get(self.get_key( data) , False ) , data) )
        
        self.cache[ key ] = { 
                                'type' : None ,
                                'near_expire' : 0, 
                                'far_expire' : 0, 
                                'last_set_expire' : 0, 
                                'addr' : copy.copy(data['addr']),
                                'device_id' : copy.copy(data['device_id']),
                                'device_type' : 'bt' ,
                                'x' : copy.copy(data['x']),
                                'y' : copy.copy(data['y']),
                                'z' : copy.copy(data['z']),
                                'received' : copy.copy( data.get('received', 0)), 
                                'lock' : threading.Lock()
                           }        
        logger.debug( self.cache.get(self.get_key( data), False)) 
      else:
        logger.debug("Using Existing Item %s : %s " % ( data.get('addr',False), self.cache.get(self.get_key( data), False ) ) )
        
      # end create
      lock = self.cache[key]['lock']
    finally:
      self.cache_lock.release()
    return lock   
     
  def filter(self,data):
    if( data.get("isexpire_message")):
      return data
    
    # ignore other packets.
    if(data.get("type", False) != "btpacket" and  data.get("type", False) != "bt_name_packet"):
      logger.debug(" filtered on packet type ")
      return {}
     
    if(not data.get("addr", False)):
      logger.debug("No address in data packet -- filtered")
      return {} 
    
    lck = self.get_lock(self.get_key(data), data)
    if(lck == None):
      logger.error("Lock should never be empty")
    try: 
      # lock each entry
      lck.acquire()
      
      logger.debug(" CACHE PRE: %s " % (self.cache) )
      # I need to setup the cache
      # maybe we should drop it out into another filter.
      if(data.get("type", False) == "btpacket" and self.determine_near(data) ): # currently near,
        logger.debug("packet was determined to be near")
        data["near"] = True
        data["prob"] = NEAR_PROB
      
        # update internal times.
        self.cache[ self.get_key( data) ]['near_expire'] = time.time() + NEAR_EXPIRE
        self.cache[ self.get_key( data) ]['far_expire']  = time.time() + FAR_EXPIRE
      
        # update NEAR and FAR expiry
        # may need to lock this.
        if(self.cache[ self.get_key( data) ]['type'] != "NEAR"):
          # ok we definitely want to update the remote site.
          logger.debug("Continued by setting it to NEAR %s %s" % (self.get_key( data),  self.cache[self.get_key( data) ]['type']))
          self.cache[self.get_key( data) ]['type'] = "NEAR"
          self.cache[ self.get_key( data)]['last_set_expire'] = time.time() # set the update here, to make it easier
          return data
      
        # set them near  
        self.cache[self.get_key( data)]['type'] = "NEAR"
      else:
        # well, if they aren't within the in threshold they must be outside of it.
        # so they must be FAR, or about to be FAR
        # or got via a name lookup
        self.cache[ self.get_key( data) ]['far_expire']  = time.time() + FAR_EXPIRE
      
        if(self.cache[ self.get_key( data) ]['near_expire'] < time.time() ):
          data["near"] = False
          data["prob"] = FAR_PROB
          self.cache[self.get_key( data)]['type'] = "FAR"

        else:
          data["near"] = True
          data["prob"] = NEAR_PROB
    
    finally:
      lck.release()
    #end locking
        
    # ok now see if we need to update:  
    #
    # for now we will always push on name update packets. [makes some sense]
    if( time.time() - self.cache[ self.get_key( data) ].get('last_set_expire',0) > UPDATE_THRESHOLD or data.get("type", False) == "bt_name_packet" ):
      logger.debug(" %s - %s > %s  - continued" % (  time.time(), self.cache[ self.get_key( data) ].get('last_set_expire',0), UPDATE_THRESHOLD))
      self.cache[ self.get_key( data)]['last_set_expire'] = time.time() # set the update here, to make it easier
      return data # if it's returned we need to update.    
    else:
      logger.debug(" %s - %s < %s so filtered packet" % (  time.time(), self.cache[ self.get_key( data) ].get('last_set_expire',0), UPDATE_THRESHOLD))
      return {}
      
    #
    # The cache CLEANUP/ EXPIRATION THREAD
    # 
    # aka, probably a future RACE condition.
    # 
  def cleanup_expire(self):
    while( not self.stopme ):
      # this is what generates the expiration code
      now = time.time()
      if(DEBUG >0 ):
        logger.debug("NOW IS: %s Checking for expiration %s" % (now, self.cache)) 
      for k in self.cache.keys():
        lck = self.cache[k]['lock']
        v = self.cache[k]
        if( v['far_expire'] <= now and self.cache[k]['type'] == "FAR"):
          # expire from now
          self.send_expire(v, "far")
          try:
            lck.acquire()
            self.cache[k]['type'] = None
          finally:
            lck.release()
             
        elif( v['near_expire'] <= now and  self.cache[k]['type'] == "NEAR"):
          # ok, just transition from near to far
          self.send_expire(v , "near")
          
          try:
            lck.acquire()
            self.cache[k]['type'] = "FAR"
          finally:
            lck.release()
          
        if( now - v['last_set_expire'] > CLEANUP_TIME and self.cache[k]['type'] == None):  
          # ok, remove old cache entries to keep it clean:
          # 
          logger.debug("REMOVING ITEM FROM EXPIRE CACHE -- Probably buggy")
          try:
            lck.acquire()          
            del self.cache[k]
          finally:
            lck.release()
      # sleep here 
      time.sleep(EXPIRE_FREQ)
    # end while      
   
  def start(self):
    self.cleanup_thread = threading.Thread(target=self.cleanup_expire)
    self.cleanup_thread.start()
    
  def send_expire(self, val, type):
    data = copy.copy(val)

    # remove the lock
    del data['lock']

    data['type'] = "expire_message"
    data['expire_time'] = time.time() 
    if(type == "far"):
      data['expire'] = time.time()
      data['prob']   = 0
    else:
      # is near
      data['expire'] = data.get('far_expire',0)  
      data['prob']   = FAR_PROB
    data["isexpire_message"] = 1    
    logger.debug("Sent expire packet: %s" % (data) )
    logger.info("Sent expire packet: %s" % (data) )
    self.core.input(data)
  
  def stop(self):
    self.stopme = True
    logger.debug("STOP CALLED ON BT AGG Filter")
 
  def __del__(self):
    self.stop()
    # stop expire thread



