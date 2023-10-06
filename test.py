import picamera
import picamera.array
import numpy as np
import time

import datetime
import time

import logging
import shutil
import os

from PIL import Image


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
motion_vectors_norm = 98    # mvecs norm
motion_density = 95         # number of pixels with |mvecs| > motion_density
motion_min_log_time = 1     # seconds
# -----------------------------------------------------------------------------------------------

# Set up logging
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

logging.basicConfig(filename=os.path.join(folder_path,'motion.log'), level=logging.INFO,
                    format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# class DetectMotion(picamera.array.PiMotionAnalysis):
#     def __init__(self, camera):
#         super(DetectMotion, self).__init__(camera)
#         self.motion_detected = False
#         self.last_detection = time.time()
#         self.last_logged = time.time()  # Add this line

#     def analyse(self, a):
#         a = np.sqrt(
#             np.square(a['x'].astype(float)) +
#             np.square(a['y'].astype(float))
#         ).clip(0, 255).astype(np.uint8)

#         if (a > motion_vectors_norm).sum() > motion_density:
#             self.motion_detected = True
#             self.last_detection = time.time()
            
#             # Only log if at least 1 second has passed since the last log
#             if self.last_detection - self.last_logged >= motion_min_log_time:
#                 logging.info('Motion detected')  # Log the detection
#                 print('Motion detected')
#                 self.last_logged = self.last_detection  # Update the last logged time

class DetectMotion(PiMotionAnalysis):
    def __init__(self, camera):
        super(DetectMotion, self).__init__(camera)
        self.motion_detected = False
        self.last_detection = time.time()
        self.last_logged = time.time()
        self.prev_frame = None  # Store the previous frame

    def analyse(self, a):
        # Convert motion data to an image
        a = np.sqrt(
            np.square(a['x'].astype(float)) +
            np.square(a['y'].astype(float))
        ).clip(0, 255).astype(np.uint8)
        
        # Convert to a PIL Image
        img = Image.fromarray(a)
        
        # Convert the image to grayscale
        gray_img = img.convert('L')
        
        # Convert back to a numpy array
        frame = np.array(gray_img)

        # If this is the first frame, save it and return
        if self.prev_frame is None:
            self.prev_frame = frame
            return
        
        # Compute absolute difference between current frame and the previous frame
        frame_diff = np.abs(frame.astype(int) - self.prev_frame.astype(int))
        
        # Update the previous frame
        self.prev_frame = frame
        
        # Threshold the difference (you may need to adjust the threshold value)
        threshold_value = 50
        frame_diff = (frame_diff > threshold_value).astype(np.uint8)
        
        # Sum the black pixels (value=0)
        black_pixel_count = np.sum(frame_diff == 0)

        # Set motion detected flag based on black pixel count threshold
        black_pixel_threshold = 1000  # Adjust this threshold value as needed
        if black_pixel_count > black_pixel_threshold:
            self.motion_detected = True
            self.last_detection = time.time()
            
            # Only log if at least 1 second has passed since the last log
            if self.last_detection - self.last_logged >= 1:
                print('Motion detected')
                self.last_logged = self.last_detection

# -----------------------------------------------------------------------------------------------

if not os.path.exists(folder_path):
    os.makedirs(folder_path)
# print('starting: ')
# target_datetime = datetime.datetime(year=2023, month=10, day=8, hour=10, minute=30, second=30)
# print(target_datetime)
# print(datetime.datetime.now())
# while datetime.datetime.now() < target_datetime:
#     time.sleep(1)
# print('done')

print("Initializing Camera...")
camera = picamera.PiCamera()
# camera.resolution = (camera_cols, camera_rows)
# camera.framerate = framerate

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
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = os.path.join(folder_path, timestamp)
        # print(f"Motion detected - total time: {int(time.time() - start_time)} - current time: {filename} {int(time.time() - output.last_detection)}")

        camera.split_recording(filename)
        output.motion_detected = False
        while (time.time() - output.last_detection) < time_motion_record and (time.time() - start_recording_time) < time_file_length:
            if camera_timestamp:
                camera.annotate_text = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
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







