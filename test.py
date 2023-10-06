import picamera
import picamera.array
import numpy as np
import time
from datetime import datetime
import logging
import shutil
import os



# -----------------------------------------------------------------------------------------------
# General setings
folder_path = '/home/pi/videos'
time_total = 4 * 60 * 60    # 4 hours
time_motion_record = 10     # 10 seconds
time_file_length = 10 * 60  # 10 minutes
camera_cols = 1920
camera_rows = 1080
framerate = 30
# i2c_bus = 10
# default_focus = 300
camera_timestamp = False
# -----------------------------------------------------------------------------------------------
# Motion sensitivity
motion_vectors_norm = 60    # mvecs norm
motion_density = 50         # number of pixels with |mvecs| > motion_density
motion_min_log_time = 1     # seconds
# -----------------------------------------------------------------------------------------------

# Set up logging
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

logging.basicConfig(filename=os.path.join(folder_path,'motion.log'), level=logging.INFO,
                    format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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

print("Initializing Camera...")
camera = picamera.PiCamera()
camera.resolution = (camera_cols, camera_rows)
camera.framerate = framerate

print("Camera Initialized")

total_disk, used_disk, free_disk = shutil.disk_usage('/home/pi/videos') # returns total, use, and free
print(total_disk)
print(used_disk)
print(free_disk)

print("Start recording...")
output = DetectMotion(camera)
camera.start_recording('/dev/null', format='h264', motion_output=output)

start_time = time.time()
summed_time = 0

# run the program until time_total
while summed_time < time_total: #time.time() - start_time < time_total:
    camera.wait_recording(0.1)
    if output.motion_detected:

        start_recording_time = time.time()
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = os.path.join(folder_path, timestamp)
        # print(f"Motion detected - total time: {int(time.time() - start_time)} - current time: {filename} {int(time.time() - output.last_detection)}")

        camera.split_recording(filename)
        output.motion_detected = False
        while (time.time() - output.last_detection) < time_motion_record and (time.time() - start_recording_time) < time_file_length:
            if camera_timestamp:
                camera.annotate_text = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
                camera.wait_recording(.1)
            camera.wait_recording(.1)
        
        # check duration
        dt = int(time.time() - start_recording_time)
        summed_time += dt
        # finish previous recording
        camera.split_recording('/dev/null')
        # rename file with duration
        os.rename(filename, filename + f"_{dt:08d}.h264")
        # print(f"Recording File Time = {dt:08d}")

        output.motion_detected = False

        total_disk, used_disk, free_disk = shutil.disk_usage('/home/pi/videos') # returns total, use, and free
        if free_disk < 5000000000:
            break

print("Stop Recording...")
camera.stop_recording()







