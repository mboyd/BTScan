#!/usr/bin/env python2.7
from tracking_method import TrackingMethod, RandomDataTracker
import socket, struct, threading, Queue, multiprocessing

PORT = 2410
MSG_MAX_LEN = 128

class ScanListener(threading.Thread):
    """Deocde receiver packet data, asynchronously.
        Provides callbacks on receipt of packets.
    """
    
    def __init__(self, addr='0.0.0.0', port=PORT):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.callbacks = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((addr, port))
        
    def add_callback(self, callback):
        self.callbacks.append(callback)

    def decode_packet(self, data):
        try:
            fields = struct.unpack('qqBBBBBBBBBBBBbxxx', data)
            tstamp_sec, tstamp_usec = fields[0:2]
            receiver_mac = ':'.join([hex(f)[2:].zfill(2) for f in fields[2:8]])
            device_mac = ':'.join([hex(f)[2:].zfill(2) for f in fields[8:14]])
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
        
                    
class TrackingThread(multiprocessing.Process):
    """Multiprocessing wrapper around TrackingMethod."""
    
    def __init__(self, method):
        multiprocessing.Process.__init__(self)
        self.daemon = True
        
        self.method = method
        self.in_queue = multiprocessing.Queue()
        self.out_queue = multiprocessing.Queue()
    
    def handle_new_data(self, data):
        self.in_queue.put(data)
    
    def get_new_position(self, timeout):
        try:
            return self.out_queue.get(True, timeout)
        except Queue.Empty:
            return None
    
    def run(self):
        while True:
            new_data = self.in_queue.get()
            new_pos = self.method.get_position(new_data)
            self.out_queue.put(new_pos)

class TrackingPipeline(object):
    """Manage a tracking pipline, handling incoming data to produce 
        a stream of position updates. Callbacks will be invoked as
        c(device, new_pos)
    """
    
    def __init__(self):
        self.scan_server = ScanServer()
        self.tracking_threads = dict()
        self.new_position_callbacks = []
        
        self.scan_server.add_new_device_callback(self.handle_new_device)
        self.scan_server.add_new_data_callback(self.handle_new_data)
        
        self.merge_thread = threading.Thread(target=self.merge_queues)
        self.merge_thread.daemon = True
        self.merge_thread.start()
    
    def add_new_position_callback(self, callback):
        self.new_position_callbacks.append(callback)
        
    def get_tracking_method(self):
        return RandomDataTracker
    
    def handle_new_device(self, device_mac):
        method_cls = self.get_tracking_method()
        method = method_cls(device_mac)
        self.tracking_threads[device_mac] = TrackingThread(method)
        self.tracking_threads[device_mac].start()
    
    def handle_new_data(self, data):
        self.tracking_threads[data[2]].handle_new_data(data)
    
    def merge_queues(self):
        while True:
            for device, tracker in self.tracking_threads.items():
                pos = tracker.get_new_position(0.1)
                if pos:
                    map(lambda c: c(device, pos), self.new_position_callbacks)
    
    
        
