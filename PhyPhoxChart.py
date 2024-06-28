import collections
from re import T
import matplotlib.axes
import matplotlib.figure
import matplotlib.lines
import constants
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart

matplotlib.use("svg")

class PhyPhoxFigure(MatplotlibChart):
    
    def __init__(self,):#fig: matplotlib.figure.Figure):
        super().__init__()
        self.expand=True
        self.experiment=0 # default experiment: Linear Acceleration
        self.offset_x, self.offset_y, self.offset_z = 0, 0, 0
        self.xlims = (0,10)
        self.figure = plt.figure(facecolor="None",figsize=(16,9))
        self.axes: list[matplotlib.axes.Axes] = [] # axes for the current experiment
        self.lines: list[matplotlib.lines.Line2D] = [] # lines for the current experiment
        self.buffer: list[collections.deque] = [] # list of buffers with phyphox data
        self.time_buffer = collections.deque() 
        self.time = [] # time buffer  
        self.cop_buffer: list[collections.deque] = [] # list of cop buffers with phyphox data 
        self.buffer_size = constants.buffer_size # initial buffer size
        self.cop_buffer_size = constants.cop_buffer_size
        self.update_buffer() # buffer for data_1 for buffer in ] 
        self.create_update_experiment_figure()
    
    # to be called everytime the limits of the x axis change
    def update_buffer(self):
        if self.buffer: self.buffer.clear()
        if self.cop_buffer: self.cop_buffer.clear()
        self.time_buffer = collections.deque(maxlen=self.buffer_size)

        for i in range(3):
            self.buffer.append(collections.deque(maxlen=self.buffer_size))
            if i<2: self.cop_buffer.append(collections.deque(maxlen=self.cop_buffer_size))
            # self.buffer.append(collections.deque(np.full(constants.buffer_size,np.nan),maxlen=self.buffer_size))
            # if i<2: self.cop_buffer.append(collections.deque(np.full(constants.buffer_size,np.nan),maxlen=self.cop_buffer_size))
    
    # to be called everytime a nex experiment is selected
    def create_update_experiment_figure(self):
        
        if self.figure.get_axes(): self.figure.clear(); self.lines.clear(); self.axes.clear(); self.update_buffer() # clear the figure if it has axes and its objects lists
        
        match self.experiment:
            case 2: # this is the Posture / Balance experiment
                n_axes = 1
            case _:
                n_axes = 3
        
        matplotlib.rcParams["font.size"] = 18
        with plt.rc_context({"axes.edgecolor":"white", "xtick.color":"white", "ytick.color":"white", "axes.facecolor":"None","axes.titlecolor":"white","axes.labelcolor":"white"}):
            for i in range(n_axes):
                self.axes.append(self.figure.add_subplot(n_axes,1, i+1))
                self.axes[i].set_title(constants.axis_title[self.experiment][i],color="white")
                line = self.axes[i].plot([],self.buffer[i],color=constants.data_colors[i])
                self.lines.append(line[0])
        
        self.offset_x, self.offset_y = 0, 0             
        xlims = (-constants.slider_initial_value[self.experiment],constants.slider_initial_value[self.experiment]) if self.experiment==2 else (0,self.buffer_size/constants.sampling_rate)
        ylims = (-constants.slider_initial_value[self.experiment],constants.slider_initial_value[self.experiment])
        
        # Lagel y and x axes
        
        plt.setp(self.axes, xlabel=constants.xlabel[self.experiment], ylabel=constants.ylabel[self.experiment])
        plt.setp(self.axes, xlim=xlims, ylim=ylims)
        plt.tight_layout()
        self.figure.canvas.draw()

    # to be called by the timer object
    def update_lines(self, t: np.ndarray, x: np.ndarray, y: np.ndarray, z: np.ndarray, w: np.ndarray):

        if self.experiment==0: N=len(t)
        else: N = min([len(t),len(x),len(y),len(z), len(t) if self.experiment==0 else len(w)])
        
        retrieved_data = self.retrieve_data_from_phyphox_response(x[:N],y[:N],z[:N],w[:N])
        self.time_buffer.extend(t[:N])
        
        if self.experiment==2:
            self.cop_buffer[0].appendleft(retrieved_data[1]); self.cop_buffer[1].appendleft(retrieved_data[0])
            self.lines[0].set(xdata=self.cop_buffer[0],ydata=self.cop_buffer[1])
        else:
            axs = self.figure.get_axes()
            for i in range(3):
                self.buffer[i].extend(retrieved_data[i])
                self.lines[i].set(xdata=self.time_buffer,ydata=self.buffer[i])
                axs[i].set(xlim=(self.time_buffer[0],t[-1]))
        
        self.update()
    
    # compute angles from quaternions
    def retrieve_data_from_phyphox_response(self, x, y, z, w):
        
        if self.experiment==0:
            return [x, y, z]
        else:
            ysqr = y * y

            t0 = +2.0 * (w * x + y * z)
            t1 = +1.0 - 2.0 * (x * x + ysqr)
            X = np.degrees(np.arctan2(t0, t1))

            t2 = +2.0 * (w * y - z * x)

            t2 = np.clip(t2, a_min=-1.0, a_max=1.0)
            Y = np.degrees(np.arcsin(t2))

            t3 = +2.0 * (w * z + x * y)
            t4 = +1.0 - 2.0 * (ysqr + z * z)
            Z = np.degrees(np.arctan2(t3, t4))    
            # print(f"x={Y-self.offset_x}, y={X-self.offset_y}, offsetX={self.offset_x}, offsetY={self.offset_y}")
            return [X-self.offset_y, Y-self.offset_x, Z-self.offset_z] 
    
       # update offset
    
    # update offset
    def update_offset(self,is_phyphox_running: bool):
       
        if is_phyphox_running:
            if self.experiment==2: # this is posture experiment (set x and y offsets)
                x = self.lines[0].get_xdata()
                if type(x)==collections.deque: 
                    self.offset_x = x[-1][0]+self.offset_x
                y = self.lines[0].get_ydata()
                if type(y)==collections.deque: 
                    self.offset_y = y[-1][0]+self.offset_y
            elif self.experiment==1:
                y = self.lines[0].get_ydata() # this is Pitch
                if type(y)==collections.deque: 
                    self.offset_y = y[-1]+self.offset_y
                x = self.lines[1].get_ydata() # this is Yaw
                if type(x)==collections.deque: 
                    self.offset_x = x[-1]+self.offset_x
                z = self.lines[2].get_ydata() # this is Roll
                if type(z)==collections.deque: 
                    self.offset_z = z[-1]+self.offset_z
            
    # update Y axes limits
    def update_y_axes_limits(self,axis_limits: float):
        
        if self.axes:
            plt.setp(self.axes,ylim=(-axis_limits,axis_limits))
            if self.experiment==2:
                plt.setp(self.axes,xlim=(-axis_limits,axis_limits))
            self.update()