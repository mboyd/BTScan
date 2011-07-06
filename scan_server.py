#!/usr/bin/env python2.7
import socket, struct

PORT = 2410
MSG_MAX_LEN = 128

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', PORT))

def decode_packet(data):
    try:
        fields = struct.unpack('qqBBBBBBBBBBBBbxxx', data)
        tstamp_sec, tstamp_usec = fields[0:2]
        host_mac_addr = ':'.join([hex(f)[2:] for f in fields[2:8]])
        dev_bt_addr = ':'.join([hex(f)[2:] for f in fields[8:14]])
        rssi = fields[14]
        return ((tstamp_sec, tstamp_usec), host_mac_addr, dev_bt_addr, rssi)
    except Exception, e:
        raise
        print 'Malformed packet; dropped'

while True:
    data, addr = sock.recvfrom(MSG_MAX_LEN)
    #print "Got data (len %i): %s" % (len(data), data)
    print str(decode_packet(data))

