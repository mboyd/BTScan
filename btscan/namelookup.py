#
# Remote scanner is a python app that listens for Bluetooth Events
#
# 
#  
#
#
import sys
import copy
import os

import random
import time
import threading
import logging
import popen2
import copy
import simplejson

from constants import *

logger = logging.getLogger("RemoteNameScanner")





class FileBTNameDriver:

  def __init__(self, _file = None):
    self.names = {}

    if(_file):
      self.names = simplejson.loads(open(_file).read())
      
  def lookup_name(self,address, device=1, timeout=10):
    #time.sleep(bt_timeout/3)
    return self.names.get(address, "Not found")

   
try:
  import bluetooth

  class Bluetoothb:
    
    def lookup_name(self,address, device=-1, timeout=10):
      """
      Linux only

      Tries to determine the friendly name (human readable) of the device with
      the specified bluetooth address.  Returns the name on success, and None
      on failure.

      timeout=10   how many seconds to search before giving up.
      """
      logger.debug("Device: %s " % (device))
      if sys.platform == "linux2":
          bluetooth._checkaddr(address)
          sock = bluetooth._gethcisock(device)
          timeoutms = int(timeout * 1000)
          try:
              name = bluetooth._bt.hci_read_remote_name( sock, address, timeoutms )
          except bluetooth._bt.error, e:
              print e
              logger.debug("Lookup Failed")
              # name lookup failed.  either a timeout, or I/O error
              name = None
          sock.close()
          return name
      elif sys.platform == "win32":
          if not bluetooth.is_valid_address(address):
              raise ValueError("Invalid Bluetooth address")

          return bluetooth.bt.lookup_name( address )

except ImportError:
  Bluetoothb = FileBTNameDriver

class Device:
  def __init__(self, devid =1, driver = Bluetoothb() ):
    self.devid = devid
    self.driver = driver
    self.lock   = threading.Lock()
    
    # a lock
    # an ID
    #  -- that's it
  
  def lookup_name(self, bd_addr):
    res = self.driver.lookup_name(bd_addr, self.devid, timeout = BT_TIMEOUT)
    if(res ==  None):
      logger.debug("Error Looking up %s" %(bd_addr))
    return res 

class FilterNameLookup(Filter):
  """
    This is adapted from some other code from SSAPP
    Essentially this class performs Bluetooth Name lookups
    and split the lookups accross an array of bluetooth devices.
    
    (
     so if you have a lot of bluetooth devices, you can spread the name lookup around,
     which are slow. 
    )
  
  """
  def __init__(self, devices = [1], btdriver = Bluetoothb):
    self.brdriver = Bluetoothb

    # I need to make sure this doesn't get too big.. 
    self.cache = {}
    self.devices = []
    self.last_cache_clear = time.time()
    
    for d in devices:
      self.devices.append(Device(d, btdriver))
  
  def clear_cache(self):
    " clears the bluetooth name cache after 24 hours"
    _now = time.time()
    todel = []
    for k,v in self.cache.items():
      if(_now - v['last'] > CACHE_CLEAR_TIME):
        todel.append(k)
    
    for i in todel:
      del self.cache[i]
      
      
  def get_device(self):
    # ok, we may have 2 devices, we may have one, but this filter will need to know
    # so we can get the device, and release it.
    # it will probably just be a lock, and a hash table.
    for d in self.devices:
      if(not d.lock.locked() ):
        return d
   
    logger.critical("Returning an empty lock, this is bad and should NEVER HAPPEN")   
    # hmm.. with only 2 threads.. this should work fine
    # 
    
  def async_lookup(self, data, callback = None):
    t = threading.Thread(target=self._async_wrapper, args=[data, callback])
    t.start()  
  
  def _async_wrapper(self, data, callback = None):
    if(callback):
      callback( self.filter(data) )
    
  def filter(self,data):
    # we'll automatically get the higher priority items first.
    # and I might want a timer to auto-lookup stuff
    logger.debug("The name lookup filter called: %s" %(data) )

    if(not data.get("addr", False) ):
      return {}

    # it's a valid packet if it gets here

    if(self.cache.get(data["addr"], False) ):
      # deal with this.. because we've seen it before
      logger.debug("We've seen: %s" %(self.cache.get(data["addr"] ) ))

      if(data.get("is_hidden", False)):
        # we are looking up a hidden name
        # so the timing should be different.
        # see if we are going to do anything with it

        # these are lower priority.. so probably won't be too big of an issue.
        if( time.time()  - self.cache[data["addr"]].get('last', 0) < HIDDEN_UPDATE_THRESHOLD):
          return {}
      else:
        # this is a normal, higher priority name lookup
        # meaning someone is near, and we want to look them up

        if (self.cache[data["addr"]].get("name", False)):
          if( time.time()  - self.cache[data["addr"]].get('last', 0) < NAME_UPDATE_THRESHOLD):
            return {}
        else:
          # we haven't got a name yet.. so check the fails.
          if( self.cache[data["addr"]].get("fails", 0)  > NAME_UPDATE_FAILED_MAX 
            and time.time() - self.cache[data["addr"]].get("last", 0) < NAME_UPDATE_FAILED_MAX_TIME):
              return {}

        # throttle it so we only check at the below frequency
        if (time.time() - self.cache[data["addr"]].get("last", 0) < NAME_UPDATE_FAILED_LAST_TIME):
          return {}          
    else:
      # new record

      logger.debug("Creating a new record for: %s" %(data["addr"]) )
      self.cache[data["addr"]] = {}
      self.cache[data["addr"]]['last'] = 0
      self.cache[data["addr"]]['fails'] = 0


    # we may get a race condition where two are run at the same time.. 
    # we might want to check for this case

    # if we get here.. we decided to do a lookup
    dev = self.get_device()
    addr = data["addr"]
    try:
      dev.lock.acquire()

      #ok we are checking it set the time.
      self.cache[data["addr"]]['last'] = time.time()

      # do a name lookup.. blocking here.. maybe with a timeout
      # get the results.
      name = dev.lookup_name(data["addr"])
      # we'll know if we got something good.
      # otherwise set a flag.
      if(name is None):
        self.cache[data["addr"]]['fails'] += 1        
        data = {}
        if(not data.get("is_hidden", False)): 
          logger.debug("Namelookup Failed for : %s" %(addr) )
      else:
        data['name_seen']   = time.time()
        data["timestamp"]   = time.time()
        data['device_name'] = name
        data['device_type'] = "bt"
        data['type'] = "bt_name_packet"

        # for the cache:
        self.cache[data["addr"]]['seen'] = time.time()
        self.cache[data["addr"]]['name'] = name
        self.cache[data["addr"]]['fails'] = 0
        if(not data.get("is_hidden", False)): 
          logger.debug("Namelookup Succeeded for : %s -> %s" %(addr, name) )
        else:
          logger.debug("Namelookup Succeeded for HIDDEN: %s -> %s" %(addr, name) )

    finally:
      dev.lock.release()   

  
    if(time.time() - self.last_cache_clear > CACHE_CLEAR_POLL):
      logger.debug("clearing cache")
      self.clean_cache()
      
    logger.debug("record saved: %s" %(self.cache.get(addr ) ) )
    return data
    #
    # end function  
    #
    


  




  
