import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate
import matplotlib.pyplot as plt

# Constants
SOUND_SPEED = 343.2  # speed of sound in air in m/s at 20 degrees Celsius
MIC_DISTANCE = 0.06  # distance between microphones in meters (60 mm)

def read_wav(file_path):
    rate, data = wavfile.read(file_path)
    return rate, data

def cross_correlation(channel1, channel2):
    corr = correlate(channel1, channel2, mode='full')
    lag = np.argmax(corr) - (len(channel2) - 1)
    return lag, corr

def calculate_distances(lags, sample_rate):
    # Calculate the time difference for each lag
    time_diffs = lags / sample_rate
    # Calculate distances from the time differences and the speed of sound
    distances = time_diffs * SOUND_SPEED
    return distances

def find_sound_source_position(lags, mic_positions):
    # This function should be filled with the algorithm to triangulate
    # the position of the sound source from the time differences.
    # The implementation of this function is complex and depends on
    # the specific geometry of the microphone array.
    pass

def plot_correlations(corr_01, corr_02, corr_03):
    plt.figure(figsize=(15, 5))
    plt.subplot(1, 3, 1)
    plt.plot(corr_01)
    plt.title('Cross-correlation between Mic 0 and Mic 1')
    plt.subplot(1, 3, 2)
    plt.plot(corr_02)
    plt.title('Cross-correlation between Mic 0 and Mic 2')
    plt.subplot(1, 3, 3)
    plt.plot(corr_03)
    plt.title('Cross-correlation between Mic 0 and Mic 3')
    plt.show()

# Load the recorded wav file
print("loading file")
file_path = 'audioClips/above.wav'
sample_rate, data = read_wav(file_path)

print("splitting into 4 channels")
# Assuming the data has 4 channels corresponding to 4 mics, and the sampling is same for all channels
channel_0 = data[:, 0]
channel_1 = data[:, 1]
channel_2 = data[:, 2]
channel_3 = data[:, 3]

print("doing cross_correlation")
# Calculate cross-correlations and lags
lag_01, corr_01 = cross_correlation(channel_0, channel_1)
lag_02, corr_02 = cross_correlation(channel_0, channel_2)
lag_03, corr_03 = cross_correlation(channel_0, channel_3)

plot_correlations(corr_01, corr_02, corr_03)

print("calculating distances between the lag")
# Calculate distances based on the lags
lags = np.array([lag_01, lag_02, lag_03])
distances = calculate_distances(lags, sample_rate)

# Define the positions of the microphones
# For example, let's assume the mics are on the corners of a square:
# mic_positions = np.array([[0,0], [1,0], [0,1], [1,1]])  # Example in meters

# Find the sound source position (this function needs to be implemented)
# sound_source_position = find_sound_source_position(lags, mic_positions)

# Output the results
print(f"Time lags: {lags}")
print(f"Distances from reference mic: {distances}")
# print(f"Estimated sound source position: {sound_source_position}")
