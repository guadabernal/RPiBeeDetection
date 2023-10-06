# ===============================================================================================
# onStartUp.py
# ===============================================================================================
# Description: Runs on startup and when called. Given the parameters at the top of the file, it
# collects data. Time units in seconds. Does not erase previous folder only adds to it.
#
# Run Command: "python onStartUp.py
#
# Written By: Guadalupe Bernal
# Date Last Eddited: 08/23/2023
# ===============================================================================================

import picamera
import picamera.array
import numpy as np
import time
from datetime import datetime
import logging
import shutil
import os
import socket
from datetime import date 
from datetime import time 

# -----------------------------------------------------------------------------------------------
# General setings
folder_path = '/home/pi/videos'
time_total = 3600
camera_cols = 640
camera_rows = 480
framerate = 30
i2c_bus = 10
default_focus = 300
camera_timestamp = True
pi_name = socket.gethostname()
pi_number = ''.join(filter(str.isdigit, pi_name))
# -----------------------------------------------------------------------------------------------
# Motion sensitivity
motion_vectors_norm = 48    # mvecs norm
motion_density = 50         # number of pixels with |mvecs| > motion_density
motion_min_log_time = 1     # seconds
# -----------------------------------------------------------------------------------------------


def init(bus, address):
    os.system("i2cset -y {} 0x{:02x} 0x02 0x00".format(bus, address))

def get_current_datetime():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def write(bus, address, value):
    value_high = (value >> 4) & 0x3F
    value_low  = (value << 4) & 0xF0
    os.system("i2cset -y {} 0x{:02x} {} {}".format(bus, address, value_high, value_low))

class Focuser:
    bus = None
    CHIP_I2C_ADDR = 0x0C

    def __init__(self, bus):
        self.focus_value = 0
        self.bus = bus
        self.verbose = False
        init(self.bus, self.CHIP_I2C_ADDR)

    def read(self):
        return self.focus_value

    def write(self, chip_addr, value):
        if value < 0:
            value = 0
        self.focus_value = value

        value = int(value)

        write(self.bus, chip_addr, value)

    OPT_BASE    = 0x1000
    OPT_FOCUS   = OPT_BASE | 0x01
    OPT_ZOOM    = OPT_BASE | 0x02
    OPT_MOTOR_X = OPT_BASE | 0x03
    OPT_MOTOR_Y = OPT_BASE | 0x04
    OPT_IRCUT   = OPT_BASE | 0x05
    opts = {
        OPT_FOCUS : {
            "MIN_VALUE": 0,
            "MAX_VALUE": 1000,
            "DEF_VALUE": 0,
        },
    }
    def reset(self,opt,flag = 1):
        info = self.opts[opt]
        if info == None or info["DEF_VALUE"] == None:
            return
        self.set(opt,info["DEF_VALUE"])

    def get(self,opt,flag = 0):
        info = self.opts[opt]
        return self.read()

    def set(self,opt,value,flag = 1):
        info = self.opts[opt]
        if value > info["MAX_VALUE"]:
            value = info["MAX_VALUE"]
        elif value < info["MIN_VALUE"]:
            value = info["MIN_VALUE"]
        self.write(self.CHIP_I2C_ADDR, value)
        if self.verbose:
            print("write: {}".format(value))

if not os.path.exists(folder_path):
    os.makedirs(folder_path)


motion_filename = os.path.join(folder_path, f'{pi_number}_{get_current_datetime()}.log')

logging.basicConfig(filename=motion_filename, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

logging.basicConfig(filename=os.path.join(folder_path,'motion.log'), level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class DetectMotion(picamera.array.PiMotionAnalysis):
    def __init__(self, camera):
        super(DetectMotion, self).__init__(camera)
        self.motion_detected = False
        self.last_detection = time.time()
        self.last_logged = time.time()  # Add this line

    def analyse(self, a):
        a = np.sqrt(
            np.square(a['x'].astype(float)) +
            np.square(a['y'].astype(float))
        ).clip(0, 255).astype(np.uint8)

        if (a > motion_vectors_norm).sum() > motion_density:
            self.motion_detected = True
            self.last_detection = time.time()
            # Only log if at least 1 second has passed since the last log
            if self.last_detection - self.last_logged >= motion_min_log_time:
                logging.info('Motion detected')  # Log the detection
                self.last_logged = self.last_detection  # Update the last logged time

# -----------------------------------------------------------------------------------------------

if not os.path.exists(folder_path):
    os.makedirs(folder_path)
print('starting')
target_datetime = datetime.datetime(year=2023, month=10, day=6, hour=1, minute=41, second=0)
print(target_datetime)
while datetime.datetime.now() < target_datetime:
    time.sleep(1)
    print(datetime.datetime.now())
print('done')
exit()


print("Initializing Camera...")
camera = picamera.PiCamera()
print("Camera Initialized")

focuser = Focuser(i2c_bus)
focuser.reset(Focuser.OPT_FOCUS)
print("Initial Focus: ", focuser.get(Focuser.OPT_FOCUS))

focuser.set(Focuser.OPT_FOCUS, int(default_focus))
print("Set Focus: ", focuser.get(Focuser.OPT_FOCUS))

camera.resolution = (camera_cols, camera_rows)
camera.framerate = framerate

print("Start recording...")
output = DetectMotion(camera)

timestamp   = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
filename    = os.path.join(folder_path, f"{pi_number}_{timestamp}")
start_time  = time.time()

camera.annotate_text_size = 16
camera.start_recording(filename, format='h264', motion_output=output)

print(f"Beginning Recording - Current time: {filename} {int(time.time())}")

while time.time() - start_time < time_total:
    camera.annotate_text = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    camera.wait_recording(0.01)

dt = int(time.time() - start_time)        # check duration

print(f"Recording File Time = {dt:08d}")
print("Stopping Recording...")
camera.stop_recording()
camera.close()
os.rename(filename, filename + f"_{dt:08d}.h264")   # rename file with duration

while True:
   time.sleep(0.5)





