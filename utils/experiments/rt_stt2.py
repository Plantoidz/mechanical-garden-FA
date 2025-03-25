from RealtimeSTT import AudioToTextRecorder
import soundfile as sf
import numpy as np
import os
from datetime import datetime

def process_text(text):
    print(text)

def on_recording_start():
    global recording_frames
    recording_frames = []

def on_recording_stop():
    global recording_frames
    if recording_frames:
        # Convert frames to numpy array
        audio_data = np.frombuffer(b''.join(recording_frames), dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
        
        # Create media/user_audio/temp directory if it doesn't exist
        os.makedirs('media/user_audio/temp', exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'media/user_audio/temp/recording_{timestamp}.wav'
        
        # Save the audio file
        sf.write(filename, audio_data, 16000)  # 16000 is the sample rate
        print(f"Saved recording to {filename}")

if __name__ == '__main__':
    utterance = ""
    recording_frames = []  # Global variable to store recording frames

    print("Wait until it says 'speak now'")
    with AudioToTextRecorder(
        on_recording_start=on_recording_start,
        on_recording_stop=on_recording_stop,
        on_recorded_chunk=lambda chunk: recording_frames.append(chunk)
    ) as recorder:
        utterance = recorder.text()

    print("Utterance is:", utterance)
        # i = 0

        # while True:
        #     recorder.text(process_text)
        #     print(f"Loop {i}")
        #     i += 1
        #     if i == 2:
        #         recorder.stop()
        #         recorder.shutdown()
        #         break