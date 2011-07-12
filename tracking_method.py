#!/usr/bin/env python

class TrackingMethod(object):
    """Abstract class representing a position estimator bound to a single remote device."""
    
    def __init__(self, device_mac):
        self.device_mac = device_mac
    
    def get_position(self, data):
        """Compute a new position estimate based on an updated dataset.
            data is a (receiver_mac, (time1, rssi1)) structure.
            Return value is a tuple (x,y).
        """
        raise NotImplementedError

import random
class RandomDataTracker(TrackingMethod):
    """Tracking method that simply returns points in a uniform distribution over [0,1)"""
    
    def get_position(self, data):
        return (random.random(), random.random())

import NLMaP, range_estimation
class NLMaPTracker(TrackingMethod):
    
    def __init__(self):
        self.receiver_positions = {'mac1' : (0, 0, 0),
                                    'mac2' : (0, 1, 0),
                                    'mac3' : (1, 1, 0),
                                    'mac4' : (1, 0, 0)]
    
    def get_position(self, data):
        
        
    