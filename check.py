import sounddevice as sd
from scipy.io.wavfile import write
import assemblyai as aai
import os

samplerate = 16000  # Sample rate in Hz
duration = 10  # Duration of recording in seconds
filename = "recorded_audio.wav"
print("Available audio devices:")
print(sd.query_devices())
DEVICE_ID = 6
print(f"Recording for {duration} seconds...")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, device=DEVICE_ID, channels=1)
sd.wait()
print("Recording finished.")
write(filename, samplerate, recording)
print(f"Audio saved to {filename}")