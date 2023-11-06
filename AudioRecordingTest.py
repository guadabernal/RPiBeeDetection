import pyaudio
import wave

RESPEAKER_RATE = 44100  # 44100 Hz
RESPEAKER_CHANNELS = 4  # 4 channels
RESPEAKER_WIDTH = 2     # 2 bytes = 16 bits

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

# run getDeviceInfo.py to get index
print("")
for i in range(0, numdevices):
  if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
    print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
  
exit()

RESPEAKER_INDEX = 1  # refer to input device id
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

stream = p.open(
            rate=RESPEAKER_RATE,
            format=p.get_format_from_width(RESPEAKER_WIDTH),
            channels=RESPEAKER_CHANNELS,
            input=True,
            input_device_index=RESPEAKER_INDEX,)

print("* recording")

frames = []

for i in range(0, int(RESPEAKER_RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("* done recording")

stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(RESPEAKER_CHANNELS)
wf.setsampwidth(p.get_sample_size(p.get_format_from_width(RESPEAKER_WIDTH)))
wf.setframerate(RESPEAKER_RATE)
wf.writeframes(b''.join(frames))
wf.close()
