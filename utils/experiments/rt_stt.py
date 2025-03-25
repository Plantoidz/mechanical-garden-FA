from RealtimeSTT import AudioToTextRecorder
import time
import signal
import sys
import contextlib
import os

class GracefulRecorder:
    def __init__(self):
        self.recorder = AudioToTextRecorder()
        self.running = False
        self._transcription = ""
        
    def start(self):
        try:
            self.recorder.start()
            self.running = True
            print("Recording started...")
        except Exception as e:
            print(f"Error starting recorder: {e}")
            self.running = False
    
    def get_transcription(self):
        """Gets the transcription without stopping the recorder"""
        if not self.running:
            return self._transcription
        
        try:
            self._transcription = self.recorder.text()
            return self._transcription
        except Exception as e:
            print(f"Error getting transcription: {e}")
            return self._transcription
    
    def stop(self):
        """Stops the recorder and returns the transcription"""
        if not self.running:
            return self._transcription
        
        # Get transcription first, before attempting to stop
        self.get_transcription()
        
        try:
            print("Stopping recorder...")
            # Wrap stop in try/except to handle connection errors
            try:
                self.recorder.stop()
                print("Recorder stopped successfully.")
            except (EOFError, ConnectionResetError, BrokenPipeError) as e:
                print(f"Expected connection error during stop: {e}")
                # This is expected sometimes, not a problem
            except Exception as e:
                print(f"Error stopping recorder: {e}")
        finally:
            self.running = False
            
        return self._transcription

def suppress_multiprocessing_errors():
    """Suppress known multiprocessing errors in stderr"""
    import os
    # Redirect stderr to /dev/null temporarily for cleanup operations
    old_stderr = sys.stderr
    dev_null = open(os.devnull, 'w')
    sys.stderr = dev_null
    try:
        yield
    finally:
        sys.stderr = old_stderr
        dev_null.close()

@contextlib.contextmanager
def handle_graceful_exit():
    recorder = GracefulRecorder()
    
    def signal_handler(sig, frame):
        print('\nReceived signal to terminate. Stopping recording...')
        with contextlib.suppress(Exception):
            text = recorder.stop()
            if text:
                print(f"Transcription: {text}")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        yield recorder
    finally:
        # Use error suppression context for cleanup operations
        if recorder.running:
            with contextlib.suppress(Exception):
                text = recorder.stop()
                if text:
                    print(f"Transcription: {text}")

if __name__ == '__main__':
    with handle_graceful_exit() as recorder:
        recorder.start()
        try:
            # Can use either timed recording or wait for keyboard interrupt
            print("Recording for 5 seconds (Ctrl+C to stop)...")
            time.sleep(5)
        except KeyboardInterrupt:
            pass  # The context manager will handle cleanup
        
        # The stop and text printing is handled by the context manager