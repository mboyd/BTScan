#!/usr/bin/env python

class TrackingMethod(object):
    """Abstract class representing a position estimator bound to a single remote device."""
    
    def __init__(self, device_mac):
        self.device_mac = device_mac
    
    def get_position(self, data):
        """Compute a new position estimate based on an updated dataset.
            data is an array of (receiver_mac, [(time1, rssi1), (time2, rssi2)])
            structures, with the newest data being at the end of the array.
            Return value is a tuple (x,y).
        """
        raise NotImplementedError

import random
class RandomDataTracker(TrackingMethod):
    """Tracking method that simply returns points in a uniform distribution over [0,1)"""
    
    def get_position(self, data):
        return (random.random(), random.random())