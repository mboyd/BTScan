from Tkinter import *
import tkMessageBox
import tkColorChooser
import tkFileDialog
import tkSimpleDialog
from PIL import Image,ImageTk
import Queue
import random
from collections import deque

class App:
 
    def __init__(self):
        
        self.root = Tk()

        self.frame = Frame(self.root,width=800,height=800)
        self.frame.pack()

        self.MainMenu()
        self.SideFrame()
        self.trackingarea = None
        self.bcolor = "red"  #color of tracking dots
        
        self.position_data = dict() 
        self.Hlength = 5  #length of visible tracking history
        self.track = None
        
        self.evt_queue = Queue.Queue()
        self.root.after(100, self.check_queue)
    
    def check_queue(self):
        try:
            item = self.evt_queue.get_nowait()
            if type(item) == str:
                self.handle_new_device(item)
            else:
                self.handle_new_position(item[0], item[1])
        except Queue.Empty:
            pass
        
        self.root.after(100, self.check_queue)
    
    def handle_new_device(self, device_mac):
        print 'New device detected: %s' % device_mac
        self.position_data[device_map] = deque([])
    
    def handle_new_position(self, device, pos):
        print 'Position update for device %s: now at %s' % (device, str(pos))
        pos_buf = self.position_data[device]
        pos_buf.append(pos)
        while len(pos_buf) > self.Hlength:
            pos_buf.popleft()
        
        self.plot_positions()
    
    def mainloop(self):
        self.root.mainloop()
        

    #create main application menu
    def MainMenu(self):

        menubar = Menu(self.root)
        self.root.config(menu=menubar)
                
        filemenu = Menu(menubar)
        menubar.add_cascade(label="file", menu=filemenu)
        filemenu.add_command(label="load map",command=self.Load_Map)
        filemenu.add_command(label="History",command=self.History)
        filemenu.add_separator()
        filemenu.add_command(label="Exit",command=self.Close)


    #create and resize canvas area for maps
    def MainCanvas(self):
        self.trackingarea = Canvas(self.frame, bg="white",width=self.image.size[0],height=self.image.size[1])
        self.trackingarea.pack(anchor=NW)

    def SideFrame(self):

        def mk_button_handler(button):
            def handle():
                self.result=tkColorChooser.askcolor()
                self.bcolor=self.result[1]
                button.config(bg=self.result[1])
            return handle
        
        self.sideframe = Frame(self.frame,width=100,height=400)
        self.sideframe.pack(side=RIGHT,expand=1,fill=BOTH)
        Label(self.sideframe, text="track").grid(row=0,column=0)
        Label(self.sideframe, text="BD_ADDR").grid(row=0,column=1)
        Label(self.sideframe, text="#_RCVR").grid(row=0,column=2)
        Label(self.sideframe, text="color").grid(row=0,column=3)
        
        self.device_list = []
        
        self.var1 = IntVar()
        self.c1 = Checkbutton(self.sideframe,variable=self.var1,command=self.cb).grid(row=1,column=0)
        Label(self.sideframe, text="track").grid(row=1,column=1)
        Label(self.sideframe, text="BD_ADDR").grid(row=1,column=2)
        b1 = Button(self.sideframe,text="color")
        b1.config(command=mk_button_handler(b1))
        b1.grid(row=1,column=3)

    #keep track of tracking enabled
    def cb(self):
        self.track = self.var1.get()



    #handle application closing
    def Close(self):
        if tkMessageBox.askokcancel("Quit","Do you really wish to quit?"):
            self.root.destroy()
    
    def History(self):
        length =  tkSimpleDialog.askinteger("Tracking History","Please input the history length",parent=self.root,minvalue=0,maxvalue=100,initialvalue=5)
        self.Hlength = length

    #handle opening the map
    def Load_Map(self):
        img_name = tkFileDialog.askopenfilename()
        if img_name == "":
            return
        self.image = Image.open(img_name)
        self.map = ImageTk.PhotoImage(self.image)
        optwindow = MapOptions(self.root)
        if not optwindow.val:
            return
        self.dimensions = optwindow.result
        self.MainCanvas()
        self.trackingarea.create_image(0,0, anchor=NW, image = self.map)
        self.trackingarea.pack(fill=BOTH, expand=1)
        
        
    def plot_positions(self):
        if not self.trackingarea:
            return
        self.trackingarea.delete("loc")
        if not self.track:
            return
        xloc,yloc = self.randomlocation()
        widthadj = self.image.size[0]/self.dimensions[1]
        heightadj = self.image.size[1]/self.dimensions[2]
        xcoordloc = xloc*widthadj
        ycoordloc = yloc*heightadj

        for device, pos_buf in self.position_data.items():
            for (x, y) in pos_buf:
                    self.trackingarea.create_rectangle(x-5, y-5, x+5, y+5, \
                                                fill=self.bcolor, tags="loc") 
        self.trackingarea.pack()
        
        
        
        
#file options dialog to define map dimensions
class MapOptions(tkSimpleDialog.Dialog):
    
    def body(self,master):
        Label(master, text="Name:").grid(row=0)
        Label(master, text="Width:").grid(row=1)
        Label(master, text="Height:").grid(row=2)
        
        self.e1 = Entry(master)
        self.e2 = Entry(master)
        self.e3 = Entry(master)
        
        self.e1.grid(row=0, column=1)
        self.e2.grid(row=1, column=1)
        self.e3.grid(row=2, column=1)
        
        return self.e1
    
    def validate(self):
        self.val = True
        return 1

    def apply(self):
        name = (self.e1.get())
        width = float(self.e2.get())
        height = float(self.e3.get())
        self.result = [name,width,height]
        
        

if __name__ == '__main__':
    import scan_server
    s = scan_server.TrackingPipeline()
    a = App()
    s.scan_server.add_new_device_callback(lambda dev: a.evt_queue.put(dev))
    s.add_new_position_callback(lambda dev, pos: a.evt_queue.put((dev, pos)))
    a.mainloop()
