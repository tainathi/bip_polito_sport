import flet as ft
import requests
import threading, time
import constants
import numpy as np
import os
import csv
from datetime import datetime

from PhyPhoxChart import PhyPhoxFigure


# this class defines all aspects to appear in the top bar
class PhyPhoxAppBar(ft.AppBar):
    
    def __init__(self, ip_address: str, port: str, phyphox_chart: PhyPhoxFigure):
        super().__init__()
        self.ip_address=ip_address
        self.port=port
        self.last_time_instant = 0 # used to threshold from when to query phyphox data
        self.phyphox_chart = phyphox_chart
        self.title=ft.Text("PhyPhox - PoliTO Sport")
        self.bgcolor=ft.colors.DEEP_ORANGE
        self.running_phyphox = False
        self.start_stop_event = threading.Event(); self.start_stop_event.set()
        self.timer = threading.Thread(target=timer_callback, args=(self.start_stop_event,phyphox_chart,self))
        self.leading=ft.IconButton(
                disabled=False,
                icon=ft.icons.MENU_ROUNDED,
                icon_color=ft.colors.WHITE,
                hover_color=ft.colors.ORANGE,
                on_click=self.open_drawer
                )
        self.actions=[
            
            # SET PORT CONTROLS
            ft.IconButton(
                    icon=ft.icons.EDIT,
                    icon_color=ft.colors.WHITE,
                    hover_color=ft.colors.ORANGE,
                    on_click=self.enable_editing_port
                ),
            ft.TextField(
                width=70,
                hint_text="port",
                value=self.port,
                content_padding=10,
                dense=True,
                filled=False,
                max_lines=1,
                border_color=ft.colors.DEEP_ORANGE,
                read_only=True,
                on_submit=self.update_port
            ),
            
            # SET IP ADDRESS CONTROLS
            ft.IconButton(
                    icon=ft.icons.EDIT,
                    icon_color=ft.colors.WHITE,
                    hover_color=ft.colors.ORANGE,
                    on_click=self.enable_editing_ip_address
                ),
            ft.TextField(
                hint_text="ip address",
                width=120,
                value=self.ip_address,
                content_padding=10,
                dense=True,
                filled=False,
                max_lines=1,
                border_color=ft.colors.DEEP_ORANGE,
                read_only=True,
                on_submit=self.update_ip_address
            ),

            # START STOP DATA STREAMING BUTTON
            ft.IconButton(
                icon=ft.icons.PLAY_ARROW_ROUNDED,
                icon_color=ft.colors.WHITE,
                hover_color=ft.colors.ORANGE,
                tooltip="start/stop data streaming",
                on_click=self.start_stop_streaming
                ),

            # CLEAR GRAPH BUTTON
            ft.IconButton(
                icon=ft.icons.DELETE_ROUNDED,
                icon_color=ft.colors.WHITE,
                hover_color=ft.colors.ORANGE,
                tooltip="clear graph",
                on_click=self.clear_graph
            ),

            # EXPORT DATA BUTTON
            ft.IconButton( # 
                icon=ft.icons.SAVE_ROUNDED,
                icon_color=ft.colors.WHITE,
                hover_color=ft.colors.ORANGE,
                tooltip="export all data in the graphs",
                on_click=self.export_data
            ),

            # REFRESH BUTTON
            ft.IconButton(
                icon=ft.icons.REFRESH_ROUNDED,
                icon_color=ft.colors.WHITE,
                hover_color=ft.colors.ORANGE,
                tooltip="check phyphox communication",
                on_click=self.refresh_page
            )
        ]
        self.text = "refresh"
    
    # check whether phyphox is ready for communicating
    def refresh_page(self, e): 
        try:
            data = requests.get(url="http://"+f"{self.ip_address}:{self.port}"+"/config",timeout=1).json()
            sensors = [1 for sensor in list.copy(data["inputs"]) if sensor["source"] == "linear_acceleration" or sensor["source"] == "attitude"] # [1, 1] if both sensors are in experiment
            print(data["inputs"][0]["outputs"])
            print(data["inputs"][1]["outputs"])
        except requests.exceptions.RequestException as err:
            e.page.dialog=get_dialog(err)
            e.page.dialog.open=True
            e.page.update()
    
    # send http request to start or stop data collection
    def start_stop_streaming(self, e):
        self.running_phyphox = not(self.running_phyphox)
         
        if self.running_phyphox:
            # self.phyphox_chart.create_update_experiment_figure()
            # self.phyphox_chart.update()
            try:
                # self.clear_graph(self)
                requests.get(url="http://"+f"{self.ip_address}:{self.port}"+"/control?cmd=start",timeout=1)
                time.sleep(0.2)
                self.timer.start()
            except requests.exceptions.RequestException as err:
                self.running_phyphox = False
                return
        else:
            self.start_stop_event.clear()
            self.start_stop_event = threading.Event(); self.start_stop_event.set()
            self.timer = threading.Thread(target=timer_callback, args=(self.start_stop_event,self.phyphox_chart, self))
            self.last_time_instant = 0
            requests.get(url="http://"+f"{self.ip_address}:{self.port}"+"/control?cmd=stop",timeout=1)
        
        if self.leading:
            self.leading.disabled = not(self.leading.disabled)
            for i in [0, 3, 4, 5]:
                e.page.controls[0].actions[i].disabled = self.running_phyphox
            e.page.controls[0].update()

        e.control.icon = ft.icons.STOP_ROUNDED if self.running_phyphox else ft.icons.PLAY_ARROW_ROUNDED
        e.control.update()

    # clear the graph 
    def clear_graph(self, e):
        try:
            requests.get(url="http://"+f"{self.ip_address}:{self.port}"+"/control?cmd=clear",timeout=1)
            self.phyphox_chart.create_update_experiment_figure()
            self.phyphox_chart.update()
        except requests.exceptions.RequestException as err:
            e.page.dialog=get_dialog(err)
            e.page.dialog.open=True
            e.page.update()
    
    # export all data on the screen
    def export_data(self, e):
        
        try:
            # retrieving all data
            response = requests.get(url="http://"+f"{self.ip_address}:{self.port}"+"/get?accX=fullX&accY=full&accZ=full&acc_time=full&x=full&y=full&z=full&w=full&t=full",timeout=1).json()
        
        except requests.exceptions.RequestException as err:
            e.page.dialog=get_dialog(err)
            e.page.dialog.open=True
            e.page.update()
            return
        
        # linear acceleration data
        t_acc = np.array(response["buffer"]["acc_time"]["buffer"])
        x_acc = np.array(response["buffer"]["accX"]["buffer"])
        y_acc = np.array(response["buffer"]["accY"]["buffer"])
        z_acc = np.array(response["buffer"]["accZ"]["buffer"])

        # attitude data
        t = np.array(response["buffer"]["t"]["buffer"])
        x = np.array(response["buffer"]["x"]["buffer"])
        y = np.array(response["buffer"]["y"]["buffer"])
        z = np.array(response["buffer"]["z"]["buffer"])
        w = np.array(response["buffer"]["w"]["buffer"])
        
        N = min([len(t),len(x),len(y),len(z),len(w)])
        t=t[:N]

        [pitch,roll,yaw] = self.phyphox_chart.retrieve_data_from_phyphox_response(x[:N],y[:N],z[:N],w[:N])
        
        if os.name == "nt": download_folder = f"{os.getenv('USERPROFILE')}\\Downloads\\"
        else: download_folder = f"{os.getenv('HOME')}/Downloads" # PORT: For *Nix systems
        
        field_names = ["time acc (s)", "x acc (m/s2)", "y acc (m/s2)", "z acc (m/s2)", "time (s)", "pitch (deg)", "roll (deg)", "yaw (deg)"]
        file_name = download_folder + "phyphox_data_" + datetime.now().strftime("%d%m%y_%H-%M-%S") + ".csv"
        
        with open(file_name, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(field_names)
            writer.writerows(np.transpose([t_acc,x_acc,y_acc,z_acc,t,pitch,roll,yaw]))

        e.page.dialog=get_dialog("Data exported to the Downloads folder\n\nFile just exported: " + file_name)
        e.page.dialog.open=True
        e.page.update()
        
    # enable text edit field for inputing ip address
    def enable_editing_ip_address(self, e):
        if self.actions != None:
            if type(self.actions[3]) == type(ft.TextField()):
                self.actions[3].filled = True
                self.actions[3].read_only = False
                self.actions[3].update()

    # update ip address and disable editing text field
    def update_ip_address(self, e):
        e.control.filled = False
        e.control.read_only = True
        e.control.update()
        self.ip_address = e.control.value
        e.page.client_storage.set("ip_address",e.control.value)
            
    # enable text edit field for inputing PORT
    def enable_editing_port(self, e):
        if self.actions != None:
            if type(self.actions[1]) == type(ft.TextField()):
                self.actions[1].filled = True
                self.actions[1].read_only = False
                self.actions[1].update()

    # update ip address and disable editing text field
    def update_port(self, e):
        e.control.filled = False
        e.control.read_only = True
        e.control.update()
        self.port = e.control.value
        e.page.client_storage.set("port",e.control.value)

    # select which experiment to try
    def open_drawer(self, e):
        e.page.drawer.open=True
        e.page.update()

    
def timer_callback(start_stop_event: threading.Event, phyphox_chart: PhyPhoxFigure, phyphox_appbar: PhyPhoxAppBar):
    
    while start_stop_event.is_set():
        
        match phyphox_chart.experiment:
            case 0:
                response = requests.get(url="http://"+f"{phyphox_appbar.ip_address}:{phyphox_appbar.port}"+f"/get?accX={phyphox_appbar.last_time_instant}|acc_time&"+
                                    f"accY={phyphox_appbar.last_time_instant}|acc_time&accZ={phyphox_appbar.last_time_instant}|acc_time&acc_time={phyphox_appbar.last_time_instant}|acc_time",
                                    timeout=1).json()
            case 1:
                response = requests.get(url="http://"+f"{phyphox_appbar.ip_address}:{phyphox_appbar.port}"+f"/get?x={phyphox_appbar.last_time_instant}|acc_time&"+
                                    f"y={phyphox_appbar.last_time_instant}|acc_time&z={phyphox_appbar.last_time_instant}|acc_time&" + 
                                    f"w={phyphox_appbar.last_time_instant}|acc_time&acc_time={phyphox_appbar.last_time_instant}|acc_time",
                                    timeout=1).json()
            case _:
                response = requests.get(url="http://"+f"{phyphox_appbar.ip_address}:{phyphox_appbar.port}"+f"/get?x&y&z&w&acc_time",
                                    timeout=1).json()
                
        phyphox_appbar.last_time_instant = response["buffer"]["acc_time"]["buffer"][-1] # updating the threshold for retrieving phyphox data
        phyphox_chart.update_lines(np.array(response["buffer"]["acc_time"]["buffer"]), # time vector
                                   np.array(response["buffer"][constants.phyphox_buffers[phyphox_chart.experiment][0]]["buffer"]), # "x, acc or quaternion"
                                   np.array(response["buffer"][constants.phyphox_buffers[phyphox_chart.experiment][1]]["buffer"]), # "y, acc or quaternion"
                                   np.array(response["buffer"][constants.phyphox_buffers[phyphox_chart.experiment][2]]["buffer"]), # "z, acc or quaternion"
                                   np.array([]) if phyphox_chart.experiment == 0 else np.array(response["buffer"][constants.phyphox_buffers[phyphox_chart.experiment][3]]["buffer"]), # "w, acc or quaternion"
                                   )
        time.sleep(1/constants.refresh_rate)
    
    
def get_dialog(text):
    return ft.AlertDialog(
        title=ft.Text(text),
        on_dismiss=lambda e: print("Dialog dismissed!")
    )