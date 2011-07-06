from Tkinter import *
import tkMessageBox
import tkColorChooser
import tkFileDialog
import tkSimpleDialog
from PIL import Image,ImageTk

class App:
 
    def __init__(self):
        
        self.root = Tk()

        self.frame = Frame(self.root,width=800,height=800)
        self.frame.pack()

        self.MainMenu()
        self.SideFrame()
        

        self.root.mainloop()
        

    #create main application menu
    def MainMenu(self):

        menubar = Menu(self.root)
        self.root.config(menu=menubar)
                
        filemenu = Menu(menubar)
        menubar.add_cascade(label="file", menu=filemenu)
        filemenu.add_command(label="load map",command=self.Load_Map)
        filemenu.add_separator()
        filemenu.add_command(label="Exit",command=self.Close)


    #create and resize canvas area for maps
    def MainCanvas(self):
        self.trackingarea = Canvas(self.frame, bg="white",width=self.image.size[0],height=self.image.size[1])
        self.trackingarea.pack(anchor=NW)

    def SideFrame(self):

        def mk_button_handler(button):
            def handle():
                result=tkColorChooser.askcolor()
                button.config(bg=result[1])
            return handle
        
        self.sideframe = Frame(self.frame,width=100,height=400)
        self.sideframe.pack(side=RIGHT,expand=1,fill=BOTH)
        Label(self.sideframe, text="track").grid(row=0,column=0)
        Label(self.sideframe, text="BD_ADDR").grid(row=0,column=1)
        Label(self.sideframe, text="#_RCVR").grid(row=0,column=2)
        Label(self.sideframe, text="color").grid(row=0,column=3)
        
        self.device_list = []
        
        var1 = IntVar()
        c1 = Checkbutton(self.sideframe,variable=var1).grid(row=1,column=0)
        Label(self.sideframe, text="track").grid(row=1,column=1)
        Label(self.sideframe, text="BD_ADDR").grid(row=1,column=2)
        b1 = Button(self.sideframe,text="color")
        b1.config(command=mk_button_handler(b1))
        b1.grid(row=1,column=3)

        
        
      
    def Color_Choose():
        pass


    #handle application closing
    def Close(self):
        if tkMessageBox.askokcancel("Quit","Do you really wish to quit?"):
            self.root.destroy()

    #handle opening the map
    def Load_Map(self):
        file = tkFileDialog.askopenfilename()
        if file == "":
            return
        self.image = Image.open(file)
        self.map = ImageTk.PhotoImage(self.image)
        optwindow = MapOptions(self.root)
        if not optwindow.val:
            return
        self.dimensions = optwindow.result
        self.MainCanvas()
        self.trackingarea.create_image(0,0, anchor=NW, image = self.map)
        self.trackingarea.pack(fill=BOTH, expand=1)
        
        
        
        
        
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
        width = int(self.e2.get())
        height = int(self.e3.get())
        self.result = [name,width,height]
        
        

   
App()
