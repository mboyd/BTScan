#!/usr/bin/env python2.7
import socket, struct, threading

PORT = 2410
MSG_MAX_LEN = 128

class ScanListener(threading.Thread):
    """Deocde receiver packet data, asynchronously.
        Provides callbacks on receipt of packets.
    """
    
    def __init__(self, addr='0.0.0.0', port=PORT):
        threading.Thread.__init__(self)
        self.callbacks = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((addr, port))
        
    def add_callback(self, callback):
        self.callbacks.append(callback)

    def decode_packet(self, data):
        try:
            fields = struct.unpack('qqBBBBBBBBBBBBbxxx', data)
            tstamp_sec, tstamp_usec = fields[0:2]
            receiver_mac = ':'.join([hex(f)[2:] for f in fields[2:8]])
            device_mac = ':'.join([hex(f)[2:] for f in fields[8:14]])
            rssi = fields[14]
            return ((tstamp_sec, tstamp_usec), receiver_mac, device_mac, rssi)
        except Exception, e:
            print 'Malformed packet (%s); dropped' % str(e)

    def run(self):    
        while True:
            data, addr = self.sock.recvfrom(MSG_MAX_LEN)
            info = self.decode_packet(data)
            for c in self.callbacks:
                c(info)


class ScanServer(object):
    """Process decoded packet data to provide higher-level tracking status.
    
        self.data is a dictionary mapping device macs to receiver dictionaries,
        each of which mapps receiver macs to a stack of the most recent contacts
        between the given device / receiver pair.
    
    """
    
    def __init__(self, *args, **kwargs):
        self.listener = ScanListener(*args, **kwargs)
        self.listener.add_callback(self.process_packet)
        
        self.devices = []
        self.receivers = []
        self.data = dict()
        
        self.i = 0  # Counter for periodic memory cleanup
        self.CLEANUP_FREQUENCY = 500
        self.MAX_DATASET = 100   # Max # points for 1 device / receiver pair
        
        self.new_device_callbacks = []
        self.new_data_callbacks = []
        
        self.listener.start()
        
    def add_new_device_callback(self, callback):
        self.new_device_callbacks.append(callback)
    
    def add_new_data_callback(self, callback):
        self.new_data_callbacks.append(callback)
    
    def process_packet(self, packet):
        tstamp, receiver_mac, device_mac, rssi = packet
        if not device_mac in self.data:
            self.data[device_mac] = {receiver_mac : [rssi]}
            self.devices.append(device_mac)
            
            map(lambda c: c(device_mac), self.new_device_callbacks)
            
        else:
            if not receiver_mac in self.data[device_mac]:
                self.data[device_mac][receiver_mac] = [rssi]
                if not receiver_mac in self.receivers:
                    self.receivers.append(receiver_mac)
            else:
                self.data[device_mac][receiver_mac].append(rssi)
        
        map(lambda c: c(packet), self.new_data_callbacks)
        
        if self.i % self.CLEANUP_FREQUENCY == 0:
            self.clean_dataset()
        self.i += 1
    
    def clean_dataset(self):
        for d in self.data.keys():
            for r in self.data[d].keys():
                data = self.data[d][r]
                if len(data) > self.MAX_DATASET:
                    del data[0:len(data)-self.MAX_DATASET]
    
        
