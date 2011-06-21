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
import os
import random
import time
import popen2
import copy
import string
import MySQLdb
import fcntl
import socket
import struct
import commands


#
# scanners:
#
SCANNER_PIPE = '/tmp/btscan'
SCANNER_PATH = './btscan'

#
#getting local mac address
#
def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
hwaddr = getHwAddr('eth1') 



class BTMonitor:
  # class to monitor BT on a device
  def __init__(self, scanner_path = SCANNER_PATH, scanner_pipe = SCANNER_PIPE):
    self.scanner_path = scanner_path
    self.scanner_pipe = scanner_pipe
    self.stopme = False
    
    
  def start(self):
    #open database connection
    self.db = MySQLdb.connect("localhost","user","gpuuser","bluetooth1")

    #prepare a cursor object
    self.cursor =self.db.cursor()
   

    # this is UDP send (the reader)
    r, w = popen2.popen2(self.scanner_path)
    ret = r.readline()
    res = ret.rstrip('\n')  # may need to change for windows
    self.btscan_pid = 999999
    try: 
      self.btscan_pid = int(res)
    except:
      self.stop()
      return
    
    f = open(self.scanner_pipe, "r")
    line = "1"
    
    while ( line != "" and not self.stopme):
      line = f.readline()
      if(line != ""):  
        self.process_line(line)      
    f.close()
    r.close()
    w.close()

  def stop(self):
    #disconnect from SQL server
    self.db.close()
    try:
      os.kill(self.btscan_pid,9)
    except OSError:
      pass
    try:
      os.wait()
    except OSError:
      pass

  def process_line(self,data):
    line =  (data,time.time())
    line = str(line).strip('[]')
    if line == "\n":
      pass
    elif line == "":
      pass
    else:
      line = [i.strip('[]\n') for i in line.split(',')]
      newline = self.process(line[0])
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
        self.cursor.execute(SQL)
      #commit changes to database
        self.db.commit()
      except:
      #rollback in case of error
        self.db.rollback()
        print "fail"

  def process(self,line):
    newline = line.split('|')
    newline = [i.strip("/n\'\\ ") for i in newline]
    return newline


#
#Setup and Run BT input
#
if __name__ == '__main__':
    btm = BTMonitor()
    try:
        btm.start()
    except KeyboardInterrupt:
        btm.stop()





