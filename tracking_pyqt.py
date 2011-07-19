# tracker_interface in PyQt
# kaycool
#

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import scan_server, config, data_packet, Mysql_logger
from PIL import Image
from collections import deque
import sys, time, Queue, random
import pickle 

class MainApp (QWidget):
    def __init__(self):
        
        #Variables
        self.device_list = dict() #contains tracking_state, color, gui_element, listed by MAC
        self.position_data = dict() 
        self.Hlength = config.TRACKING_HISTORY # length of visible tracking history
        self.evt_queue = Queue.Queue() # queue of data streaming from mysql(?)
	self.packet_buf = None #
        
        ### GUI SETUP ###
        QMainWindow.__init__(self)
        
        self.resize (800, 600)
        self.setWindowTitle('Tracker')
        
        # Menu
        # Create actions
        quit = QAction('Quit', self)
        quit.setShortcut('Ctrl+Q')
        quit.setStatusTip('Exit Application')
        self.connect(quit, SIGNAL('triggered()'), SLOT('close()'))

        loadMap = QAction('Load Building', self)
        loadMap.setShortcut('Ctrl+o')
        loadMap.setStatusTip('Load Building')
        self.connect(loadMap, SIGNAL('triggered()'), self.mapOpen)        

        showRSSI = QAction('Show RSSI', self)
        showRSSI.setShortcut('Ctrl+r')
        showRSSI.setStatusTip('Show RSSI')
        self.connect(showRSSI, SIGNAL('triggered()'), self.showRSSI)
        
        history = QAction('History', self)
        history.setShortcut('Ctrl+h')
        history.setStatusTip('History')
        self.connect(history, SIGNAL('triggered()'), self.History)


        
     
       
       
        # Remove highlighted tab
        rmTab = QAction('Remove Map', self)
        rmTab.setShortcut('Ctrl+w')
        rmTab.setStatusTip('Remove Map')
        self.connect(rmTab, SIGNAL('triggered()'), self.rmCurTab)
        
        # Rename highlighted tab
        rnTab = QAction('Rename Map', self)
        # rnTab.setShortcut('Ctrl+w')
        rnTab.setStatusTip('Rename Map')
        self.connect(rnTab, SIGNAL('triggered()'), self.rnCurTab)

	 # Tabs
        self.mainTab = QTabWidget()
        self.sideTab = QTabWidget()        
        tab1 = Map(self)
        tab2 = QLabel()
        tab3 = QTableWidget()
        tab4 = QLabel()

        
        # Initialize menu bar, set menu options
        menubar = QMenuBar()
        file = menubar.addMenu('&File')
	maps = menubar.addMenu('&Map')
        file.addAction(loadMap)
        file.addAction(showRSSI)
        file.addAction(history)
        file.addAction(quit)
        maps.addAction(rmTab)
        maps.addAction(rnTab)
        
        # Set tab layouts

        self.mainTab.addTab(tab1, "Main")
        self.sideTab.addTab(tab3, "Tribe")
        self.sideTab.addTab(tab4, "Other")
        
        self.mainFrame = QVBoxLayout()
        self.mainFrame.addWidget(self.mainTab)
        self.sideFrame = QVBoxLayout()
        self.sideFrame.addWidget(self.sideTab)

        frame2 = QHBoxLayout()
        frame2.addLayout(self.mainFrame, 2)
        frame2.addLayout(self.sideFrame, 1)
        frame1 = QVBoxLayout()
        frame1.addWidget(menubar)
        frame1.addLayout(frame2)
            
       #self.trackingArea = QWidget(self)
        self.createSideMenu()
        
        self.setLayout(frame1)
        
        # Creates box for raw data dump; show with showRSSI()
        self.RSSI = QWidget()
        self.RSSI.resize(300, 200)
        self.RSSI.setWindowTitle('RSSI')
        

        self.rssi_plot = None # necessary?
        
        self.add_device('0.0.0.0') #TEST
	

	
    def mapOpen(self): # Loads map in current tab
    	filename = QFileDialog.getOpenFileName(self, 'Open file')
	f=open(filename).readline()
	
	fp=f.rstrip()
	fp=fp.strip('\'')+'.p'
	execfile(filename.__str__())
	building=pickle.load(open (fp))
	for floor in building.floors:
		self.addTab(floor.name, floor.file_name)

		
        tw = self.mainTab
	
        
    def History(self):
        length = QInputDialog.getInt(self, "Tracking History",
                                      "Please input the history length", value=5,
                                      min=0)
        self.Hlength = length

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
            'Are you sure you want to quit?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
    def addTab(self, name, image):	
	new = QLabel()
	tw=self.mainTab
        tw.addTab(new, str(name))
	pmap= QPixmap(str(image)).scaled(tw.size())
	new.setPixmap(pmap)
    
    def rmCurTab(self):
        self.mainTab.removeTab(self.mainTab.currentIndex())
        
    def rnCurTab(self):
    	input = QInputDialog(self)
    	input.setLabelText('New name?')
    	newName = QInputDialog.getText(self, 'Rename Tab', 'New name?')
    	if str(newName[0]) != "": 
    		mt = self.mainTab
    		mt.setTabText(mt.currentIndex(), str(newName[0]))

    def showRSSI(self):
        
        self.RSSI.show()
        # TODO: pipe raw data to this window


    def createSideMenu(self):
        print "creating side menu"
        tribe = self.sideTab.widget(0)
        tribe.setHorizontalHeaderLabels(["track", "BD_ADDR", "#_RCVR", "COLOR"])
        tribe.setColumnWidth(0, 40)
        tribe.setColumnWidth(1, 100)
        tribe.setColumnWidth(2, 45)
        tribe.setColumnWidth(3, 50)

   
       
       
    ##### DEVICE HANDLING METHODS #####
     
    # Checks queue for new packets (?)
    def check_queue(self):
        try:
             while True:
                item = self.evt_queue.get_nowait()
                if type(item) == str:
                    self.handle_new_device(item)
                else:
                    self.handle_new_position(item)
        except Queue.Empty:
        	pass
	self.mainTab.widget(0).update()
        
            # self.root.after(config.POLL_PERIOD, self.check_queue) # FIXME
    # adds necessary information for a new device (device_list, position_data)
    def handle_new_device(self, device_mac):
         print 'New device detected: %s' % device_mac
         self.position_data[device_mac] = deque([])
         self.add_device(device_mac)
        
   
     # Adds new device being tracked to side frame   
    def add_device(self, device_mac):
                    
        def mk_button_handler(button, color):
            def handle():
                # FIXME
                #result = tkColorChooser.askcolor()
                QColorDialog.getColor(Qt_red, self)
                color[:] = list(result[1])
                button.config(bg=result[1])
            return handle

        row = len(self.device_list) + 1
              
        ### Add new device in sidebar
        tribe = self.sideTab.widget(0)
        
        checkbox = QCheckBox()
        checkbox.setCheckState(True)
        #tribe.setItem(row, 0, QTableWidgetItem(QCheckBox())) 
        # TODO: set to emit signal readable by drawer?
        
        tribe.setItem(row, 1, QTableWidgetItem(device_mac))
        
        tribe.setItem(row, 2, QTableWidgetItem("#"))
        
        #tribe.setItem(row, 3, QColorDialog) # FIXME
        # should be colored button that opens color dialog
        
        
        # Add device to stored dictionary
        #self.device_list[device_mac] = (checkbox.isChecked(), color, (checkbox, L1, L2, colorbutton))

    def add_packet(self, packet):
        #floor=self.mainTab.indexOf(packet.floor)
        # for now, only uses tab1
        
        tab1.paintEvent(QPaintEvent(self))
                
        #handle lack of map

    def handle_new_position(self, packet):
        if not packet.device_mac in self.position_data:
            self.handle_new_device(packet.device_mac)
        
        self.packet_buf = self.position_data[packet.device_mac]
        self.packet_buf.append(packet)
        
        while len(self.packet_buf) > self.Hlength:
            
            self.packet_buf.popleft()
	
        
    ##remove_packet
    
class Map(QLabel):

    #pathname is the pathname of the map file
    # dList 
    def __init__ (self, main):
        super(Map, self).__init__()
        pm = QPixmap('test-grid.gif').scaled(self.size())
        self.setPixmap(pm)
	self.m=main
	self.time=1
        
    #e: event
    def paintEvent(self, e):
        painter = QPainter();        
        painter.begin(self)
        painter.drawPixmap(10, 10, QPixmap('test-grid.gif'));
     	self.drawPoints(painter)
        painter.end()
    def drawPoints(self, qp):
	qp.setBrush(QColor(255, 0, 0, 80))
	qp.setPen(Qt.red)
	for i in range(len(self.m.packet_buf)):
            x,y = self.m.packet_buf[i].position
            qp.drawEllipse(x*400, y*400,5,5)

 
        
#file options dialog to define map dimensions
# TODO: adapt to PyQt
#class MapOptions(tkSimpleDialog.Dialog):

    #def __init__(self, parent, callback):
       # self.callback = callback
       # tkSimpleDialog.Dialog.__init__(self, parent)
    
    #def body(self,master):
       # Label(master, text="Name:").grid(row=0)
        #Label(master, text="Width:").grid(row=1)
        #Label(master, text="Height:").grid(row=2)
        
        #self.e1 = Entry(master)
        #self.e2 = Entry(master)
       #self.e3 = Entry(master)
        
       # self.e1.grid(row=0, column=1)
        #self.e2.grid(row=1, column=1)
       # self.e3.grid(row=2, column=1)
        
       # return self.e1
    
   # def validate(self):
        #self.val = True
       # return 1

    #def apply(self):
       # self.callback(self)

# TODO: resize map in response to window resize

# Run application


app = QApplication(sys.argv)
main = MainApp()
s = scan_server.TrackingPipeline()
s.scan_server.add_new_device_callback(lambda dev: main.evt_queue.put(dev))
s.add_new_position_callback(lambda packet: main.evt_queue.put(packet))
main.show()
t=QTimer(main)
main.connect(t, SIGNAL("timeout()"), main.check_queue)
t.start(100)


sys.exit(app.exec_())



   

        
        

        ##############################
        # Things to add               #
        # iconsize, toolButtonStyle  #
        ##############################