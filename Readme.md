#BTScan
Bluetooth-based wireless positioning.

##Dependencies
- python-matplotlib
- python-numpy

##Usage
`btscan.c` contains the receiver code, which forwards timestamped RSSI data over the network to a central server.  `scan_server.py` contains a sketch of the server code, enough to collect rough data for analysis.  `plotter.py` and `process.py` may be useful in analyzing raw data, while `btscanner.py` is an obsolete receiver script and will be removed soon.
