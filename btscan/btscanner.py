#
# Remote scanner is a python app that listens for Bluetooth Events
# in a manner similar to udpsend.rb from the Nokia Code
#
# 
#  
#
#
import sys
sys.path.append('.')

import copy
import os
import logging

import random
import time
import threading
import logging
import popen2
import copy
import string
import MySQLdb

from constants import *


logger = logging.getLogger("RemoteScanner")

# scanners:
SCANNER_PIPE = '/tmp/btscan'
SCANNER_PATH = os.path.dirname(__file__) +'/btscan'

try:
  import bluetooth
except:
  class FakeBluetooth:
    def __is_valid_address(self,device):
      return True
    is_valid_address = classmethod(__is_valid_address)    
  bluetooth = FakeBluetooth


class BTMonitor:
  # class to monitor BT on a device
  def __init__(self, scanner_path = SCANNER_PATH, scanner_pipe = SCANNER_PIPE):
    self.scanner_path = scanner_path
    self.scanner_pipe = scanner_pipe
    self.stopme = False
    

    
  def start(self,callback):
   

    # this is UDP send (the reader)
    logger.debug("open monitor: %s" % (self.scanner_path))
    r, w = popen2.popen2(self.scanner_path)
    logger.debug("after opening monitor")
    ret = r.readline()
    logger.debug("written line is: %s" % (ret))
    res = ret.rstrip('\n')  # may need to change for windows
    self.btscan_pid = 999999
    try: 
      self.btscan_pid = int(res)
    except:
      logger.error("failed to launch btscan")
      self.stop()
      return
    
    logger.debug("scanner PID: %s" % (self.btscan_pid))
    # something here to wait.
    # might even be able to put the consumer.. reader here.
    f = open(self.scanner_pipe, "r")
    line = "1"
    
    while ( line != "" and not self.stopme):
      line = f.readline()
      if(line != ""):
        # do stuff
        logger.debug("READ %s" % (line))  
        callback(line)
    logger.debug("Ended reading from file")      
    f.close()
    r.close()
    w.close()

  def stop(self):
    logger.debug("STOPPING REMOTE NAME SCANNER")
    self.stopme = True
    #disconnect from SQL server
    db.close()
    try:
      os.kill(self.btscan_pid,9)
    except OSError:
      logger.debug("Couldn't kill %s " % ( self.btscan_pid))
    logger.debug("before OS wait")
    try:
      os.wait()
    except OSError:
      logger.debug("OS wait failed %s " % ( self.btscan_pid))
      





