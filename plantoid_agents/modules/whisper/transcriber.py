from RealtimeSTT import AudioToTextRecorder
import soundfile as sf
import numpy as np
import os
from datetime import datetime

class WhisperTranscriber:
    def __init__(self):
        self.recording_frames = []
        self.recorder = None

    def _on_recording_start(self):
        self.recording_frames = []

    def _on_recording_stop(self):
        if self.recording_frames:
            # Convert frames to numpy array
            audio_data = np.frombuffer(b''.join(self.recording_frames), dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            
            # Create media/user_audio/temp directory if it doesn't exist
            os.makedirs('media/user_audio/temp', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'media/user_audio/temp/recording_{timestamp}.wav'
            
            # Save the audio file
            sf.write(filename, audio_data, 16000)  # 16000 is the sample rate
            print(f"Saved recording to {filename}")

    def transcribe(self):
        """
        Transcribe speech using the Whisper model.
        Returns the transcribed text.
        """
        with AudioToTextRecorder(
            on_recording_start=self._on_recording_start,
            on_recording_stop=self._on_recording_stop,
            on_recorded_chunk=lambda chunk: self.recording_frames.append(chunk)
        ) as recorder:
            return recorder.text()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.recorder:
            self.recorder.shutdown() 