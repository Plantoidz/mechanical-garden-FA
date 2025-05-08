from RealtimeSTT import AudioToTextRecorder
import soundfile as sf
import numpy as np
import os
import time
import threading
from datetime import datetime

class WhisperTranscriber:
    def __init__(self, timeout_seconds=None, compute_type="float32"):
        self.recording_frames = []
        self.recorder = None
        self.timeout_seconds = timeout_seconds
        self.timeout_thread = None
        self.is_recording = False
        self.compute_type = compute_type

    def _on_recording_start(self):
        self.recording_frames = []
        self.is_recording = True
        
        # Start timeout thread if timeout is specified
        if self.timeout_seconds is not None:
            self.timeout_thread = threading.Thread(target=self._timeout_handler)
            self.timeout_thread.daemon = True
            self.timeout_thread.start()

    def _timeout_handler(self):
        """Stop recording after timeout_seconds"""
        time.sleep(self.timeout_seconds)
        if self.is_recording and self.recorder:
            self.recorder.stop_recording()
            self.is_recording = False

    def _on_recording_stop(self):
        self.is_recording = False
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
            on_recorded_chunk=lambda chunk: self.recording_frames.append(chunk),
            silero_deactivity_detection=True,
            enable_realtime_transcription=True,
            use_main_model_for_realtime=True,
            silero_sensitivity=0.4,
            post_speech_silence_duration=1.5,
            min_length_of_recording=3.5,
            compute_type=self.compute_type
        ) as recorder:
            self.recorder = recorder
            return recorder.text()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.recorder:
            self.recorder.shutdown() 