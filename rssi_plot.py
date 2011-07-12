import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import Tkinter as Tk
from collections import deque
import threading

class RSSIPlot(object):

    def __init__(self, device_mac):
        self.device_mac = device_mac
        self.receiver_plots = dict()

        self.window = Tk.Toplevel()

        self.figure = Figure()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        
        

    def plot_point(self, packet):
        if not packet.receiver_mac in self.receiver_plots:
            i = len(self.receiver_plots) + 1
            ax = self.figure.add_subplot(7, 1, i)
            line, = ax.plot(range(10), range(10), animated=True, lw=2)
            self.receiver_plots[packet.receiver_mac] = (ax, line, [], [])
            self.canvas.draw()

        ax, line, xdata, ydata = self.receiver_plots[packet.receiver_mac]
        xdata.append(packet.timestamp[0])
        ydata.append(packet.rssi)
        line.set_data(xdata, ydata)

        #ax.draw_artist(line)
        self.figure.canvas.blit(ax.bbox)
        
        
