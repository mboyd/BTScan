import logging
import sys
import os
import time
import MySQLdb
import pickle
import fcntl
import socket
import struct

import commands
import simplejson
import urllib

from optparse import OptionParser

from btscan.proximitydetection  import FilterAddExpiration
from btscan.btscanner           import BTMonitor, SCANNER_PATH
from btscan.constants           import *




# use stream for output
logging.getLogger('').addHandler(logging.StreamHandler())
logger = logging.getLogger('NearFarScanner')

#open database connection
db = MySQLdb.connect("localhost","user","gpuuser","bluetooth1")

#prepare a cursor object
cursor = db.cursor()


parser = OptionParser()
parser.set_description("""
This program will call a URL with information about bluetooth devices that have been detected nearby
it is designed to help you quickly prototype applications that require proximity detection.  Only state changes
(i.e. arrivals and departures ) will be sent to the URL.

See the examples/ directory to learn more about what you can do with bluetooth_scanner.py
""")
parser.add_option("--devices", dest="devices", help="Number of Bluetooth devices to use for name lookups", type='int' , default = None)

parser.add_option("-v", dest="verbose",help="Verbose"           , default = False, action="store_true")
parser.add_option("--vv", dest="very_verbose",help="Very Verbose"           , default = False, action="store_true")

# for daemon
parser.add_option("--pid", dest = "pid_file", help="Pid filename", default= PID_PATH + "/bt_scanner.pid")
parser.add_option("-d", dest="daemon",help="Damonize"           , default = False, action="store_true")

parser.add_option("-l", dest="location",help="Location x,y,z"           , default = "-1,-1,-1" )

parser.add_option("--url", dest="callback_url",help="URL to be called on events"           , default = None )
parser.add_option("--output", dest="output_file",help="File to write output to"           , default = None )
parser.add_option("--input", dest="input_file",help="Read bluetooth from file instead of device"           , default = None )
parser.add_option("--names_file", dest="names_file",help="Read bluetooth from file instead of device"           , default = None )
parser.add_option("--loop", dest="loop",help="Number of times to loop the input file (use -1 to loop forever)", default = 1 )
parser.add_option("--raw", dest="raw",help="Send all Bluetooth packets without determining proximity", action="store_true", default = None )



(options, args) = parser.parse_args()

# get devices if we can
(status,hcitool_output) = commands.getstatusoutput("hcitool dev")
  

if(not options.input_file):
  # if we aren't inputing from a file, make sure we have bluetooth devices
  
  if(not os.path.exists(SCANNER_PATH)):
    logger.error("%s does not exist, please make sure you have run 'make' " % (SCANNER_PATH))
    exit(2)

  if(status !=0):
    logger.error("bluez-utils are not installed or bluetooth is not configured corectly")
    exit(2)    

  if(hcitool_output.count("\n") ==0):
    logger.error("No bluetooth devices detected")
    exit(2)    


if(hcitool_output.count("\n") ==1 and not options.names_file):
  logger.error("Name lookups will be disabled, only one bluetooth device detected")


if(options.very_verbose):
  logging.getLogger('').setLevel(logging.DEBUG)
else:
  logging.getLogger('').setLevel(logging.INFO)

# Daemon code:
if(options.daemon):
  import resource
  maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
  if maxfd == resource.RLIM_INFINITY:
    maxfd = 1024
  for fd in range(0, maxfd):
    try:
      os.close(fd)
    except OSError:  
      pass
  REDIRECT_TO = os.devnull
  os.open(REDIRECT_TO, os.O_RDWR) 
  os.dup2(0, 1) # stdout
  os.dup2(0, 2) # stderr

  pid = os.fork()
  if pid == 0:
    pass
  else:
    os._exit(0)
  
  # write pidfile:
  file(options.pid_file,"w").write("%d" % os.getpid())


options.location = [int(i) for i in options.location.split(",")]

if(not options.devices):
  options.devices = hcitool_output.count("\n")

if(options.devices > hcitool_output.count("\n")):
  options.devices = hcitool_output.count("\n")

_devices = [i for i in range(1,options.devices)]


#
# Everything about this line is mostly argument processing.
# --------------------------------------------------
# Everything below this line is doing actual work on bluetooth results.
#

#
#getting local mac address
#
def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
hwaddr = getHwAddr('eth1')   
#
# Setup BT input
#
btm = BTMonitor()

#
# Handle expirations
#

expire_filter    = FilterAddExpiration( NORMAL_EXPIRE, HIDDEN_EXPIRE)

#
#Output Raw data
#
def process_line(data):
  line =  (data,time.time())
  line = str(line).strip('[]')
  if line == "\n":
    pass
  elif line == "":
    pass
  else:
    line = [i.strip('[]\n') for i in line.split(',')]
    newline = process(line[0])
    rssi = int(newline[1])
    timestr = line[1].strip()
    timestr = timestr.strip(')')
    timef = float(timestr)
    newline[0] = newline[0].strip('(').strip("'").strip()
    data = (newline[0],rssi,timef,hwaddr)
    print data
    SQL = "INSERT INTO bluetoothTb1 (bdaddr,rssi,time,hwaddr) Values('%s','%d','%d','%s')"  % (data[0],data[1],data[2],data[3])
                
    try:
      #execute SQL command
      cursor.execute(SQL)
      #commit changes to database
      db.commit()
    except:
      #rollback in case of error
      db.rollback()
      print "fail"
  

def process(line):
    newline = line.split('|')
    newline = [i.strip("/n\'\\ ") for i in newline]
    return newline

 
#
# Start the scanner, we are good to go.
#  

btm.start( process_line )
