import pyaudio
import audioop
from collections import deque
import time

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
THRESHOLD = 30  # The threshold intensity that must be exceeded to consider it speech
SILENCE_LIMIT = 2  # Silence limit in seconds. The max amount of seconds where only silence is recorded.

def main():
    audio = pyaudio.PyAudio()

    # Start streaming
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Listening...")

    # Buffer to store audio samples
    silence_buffer = deque(maxlen=int(SILENCE_LIMIT * RATE / CHUNK))

    try:
        while True:
            # Read data from the stream
            data = stream.read(CHUNK)
            # Calculate the rms level
            rms = audioop.rms(data, 2)

            # Maintain a rolling buffer of sound levels
            silence_buffer.append(rms)

            # Check if the average over the buffer is greater than the threshold
            if sum(silence_buffer) / len(silence_buffer) > THRESHOLD:
                print("Speech detected")
            else:
                print("Silence or background noise")
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Finished recording")

    finally:
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        audio.terminate()

if __name__ == '__main__':
    main()
