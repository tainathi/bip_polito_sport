ymin,ymax = -10, 10

phyphox_buffers = [["accX","accY","accZ"], # experiment 0: Linear Acceleration
               ["x","y","z","w"], # experiment 1: Orientation
               ["x","y","z","w"]]
experiments_title = ["Linear Acceleration", "Orientation", "Posture / Balance"]

refresh_rate = 4
sampling_rate = 100
buffer_size = 1000
cop_buffer_size = 2*refresh_rate

data_colors = [(0.2, 1.0, 0.2),"cyan","yellow"]

axis_title = [["Linear Acceleration x", "Linear Acceleration y", "Linear Acceleration z"], # experiment 0
              ["Pitch", "Yaw","Roll"],
              ["Statokinesigram"]]
xlabel = ["Time (s)","Time (s)","Medio-Lateral (deg)"]
ylabel = ["(m/s\u00b2)","(degree)","Anterior-posterior (deg)"]
slider_unit = ["m/s\u00b2","deg","deg"]
slider_minmax_value = [80, 200, 50]
slider_initial_value = [10, 180, 10]