import pyaudio
import wave
import numpy as np
import pygame
import random
import os

# Parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
THRESHOLD = 1500  # Adjust this based on your needs

# Initialize PyAudio
p = pyaudio.PyAudio()

# Function to play a continuous tone
def play_tone(stream, frequency=440.0, duration=10):
    samples = (np.sin(2 * np.pi * np.arange(RATE * duration) * frequency / RATE)).astype(np.float32)
    stream.write(samples.tobytes())

# Function to play a random MP3 file
def play_random_mp3(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
    random_file = random.choice(files)
    pygame.mixer.music.load(os.path.join(folder_path, random_file))
    pygame.mixer.music.play()

# Open stream for microphone input
stream = p.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK)

# Open stream for playing the tone
tone_stream = p.open(format=pyaudio.paFloat32, channels=1,
                     rate=RATE, output=True)

# Initialize pygame for MP3 playback
pygame.init()
pygame.mixer.init()

try:
    print("Starting tone...")
    while True:
        play_tone(tone_stream, 440, 1)  # Play A4 note
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        if np.abs(data).max() > THRESHOLD:
            print("Threshold exceeded, playing random MP3.")
            play_random_mp3(os.getcwd()+'media/ambient1.mp3')  # Adjust path as needed
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
except KeyboardInterrupt:
    print("Program interrupted by user.")

finally:
    # Stop and close the streams
    stream.stop_stream()
    stream.close()
    tone_stream.stop_stream()
    tone_stream.close()
    p.terminate()
    pygame.quit()
