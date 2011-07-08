
DEFAULT_MAP = 'test-grid.gif'  #what map is loaded by default
DEFAULT_MAP_DIMENSIONS = ('default',1,1)

TRACKING_ENABLED = False #program initializes with tracking enabled
TRACKING_HISTORY = 100

DATA_FREQ = 30  #number of data points per second
MYSQL_LOGGING = False  #enable mysql database logging
POLL_PERIOD = 20

RECEIVER_POSITIONS = {'mac1' : (0, 0, 0),
                      'mac2' : (0, 1, 0),
                      'mac3' : (1, 1, 0),
                      'mac4' : (1, 0, 0),
                      'mac5' : (.5, .5, 0),
                      'mac6' : (1, 2, 0),
                      'mac7' : (2, 1, 0)}
