from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone, DeepgramClientOptions
from dotenv import load_dotenv
from websockets import WebSocketException
import logging, verboselogs
import time
import random
from playsound import playsound
from ctypes import *
from contextlib import contextmanager
import os
import sys

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plantoid_agents.lib.microphone import ModifiedMicrophone

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

@contextmanager
def ignoreStderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)

    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)

class DeepgramTranscription:
    def __init__(self, sample_rate: int = 48000, device_index: int = None, channels: int = 1, timeout: int = 5, callback=None, max_retries=50):
        self.deepgram = DeepgramClient()

        config = DeepgramClientOptions(
            options={"keepalive": "true"} # Comment this out to see the effect of not using keepalive
        )
        
        deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)

        self.is_finals = []
        self.final_result = ""
        self.transcription_complete = False  # New flag for completion
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.timeout = timeout  # Timeout in seconds
        self.callback = callback  # Callback for real-time updates
        self.max_retries = max_retries  # Max retries for restarting
        self.retry_count = 0  # Track retry attempts

    def reset(self):
        """
        Resets the state variables to their initial conditions.
        """
        self.is_finals = []
        self.final_result = ""
        self.transcription_complete = False
        
    def on_message(self, *args, **kwargs):
        result = kwargs.get('result', None)
        if result is None and args:
            result = args[0]  # Assuming result is the first positional argument

        # print("result is", result)
        sentence = result.channel.alternatives[0].transcript
        if not sentence:
            return

        if result.is_final:
            self.is_finals.append(sentence)

            if result.speech_final:
                if len(self.is_finals) > 0:
                    self.final_result = ' '.join(self.is_finals)
                    # print(f"Deepgram Utterance End: {self.final_result}")
                    print(f"\033[90m\tSpeech Final: {self.final_result}\033[0m")

                    if self.callback:
                        self.callback(self.final_result, final=True)
            else:
                print(f"\033[90m\tAlmost Final: {sentence}\033[0m")

                if self.callback:
                    self.callback(self.final_result, final=False)
        else:
            print(f"\033[90m\tInterim Results: {sentence}\033[0m")

            if self.callback:
                self.callback(self.final_result, final=False)

    def on_metadata(self, *args, **kwargs):
        metadata = kwargs['metadata'] 
        print(f"Deepgram Metadata: {metadata}")

    def on_speech_started(self, *args, **kwargs):
        print(f"\033[91m\tDetected Speech Started - Deepgram is listening...\033[0m")

    def on_utterance_end(self, *args, **kwargs):
        if len(self.is_finals) > 0:
            self.final_result = ' '.join(self.is_finals)
            # print(f"Deepgram Utterance End: {self.final_result}")
            self.is_finals = []
            self.transcription_complete = True

    def on_close(self, *args, **kwargs):
        print(f"\033[91m\tDeepgram Connection Closed\033[0m")

    def on_error(self, *args, **kwargs):
        # error = kwargs['error'] 
        print(f"Deepgram Handled Error: {kwargs}")

    def on_unhandled(self, *args, **kwargs):
        unhandled = kwargs['unhandled'] 
        print(f"Deepgram Unhandled Websocket Message: {unhandled}")

    def start_listening(self, step: int = 0):
        while self.retry_count < self.max_retries:
            try:
                print(f"\033[90m\tStarting deepgram... (Attempt {self.retry_count + 1}/{self.max_retries})\033[0m")
                self.reset()

                connection = self.deepgram.listen.live.v("1")
                connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
                connection.on(LiveTranscriptionEvents.SpeechStarted, self.on_speech_started)
                connection.on(LiveTranscriptionEvents.UtteranceEnd, self.on_utterance_end)
                connection.on(LiveTranscriptionEvents.Close, self.on_close)
                connection.on(LiveTranscriptionEvents.Error, self.on_error)
                connection.on(LiveTranscriptionEvents.Unhandled, self.on_unhandled)

                options = LiveOptions(
                    model="nova-2",
                    language="en-US",
                    smart_format=True,
                    encoding="linear16",
                    channels=self.channels,
                    sample_rate=self.sample_rate,
                    interim_results=True,
                    utterance_end_ms="1000",
                    vad_events=True,
                    endpointing=300
                )

                if not connection.start(options):
                    print("Failed to connect to Deepgram")
                    return

                microphone = ModifiedMicrophone(
                    connection.send,
                    input_device_index=self.device_index,
                    rate=self.sample_rate,
                    channels=self.channels,
                )

                microphone.start()
                start_time = time.time()

                while not self.transcription_complete or (time.time() - start_time) < self.timeout:
                    time.sleep(0.1)

                directory = os.path.join(os.getcwd(), "media/user_audio/temp")
                os.makedirs(directory, exist_ok=True)
                audio_file_path = os.path.join(directory, f"temp_reco_dg_{str(step)}.wav")

                microphone.finish(audio_file_path=audio_file_path)
                connection.finish()

                break  # Exit the loop if everything went well

            except WebSocketException as e:
                print(f"WebSocketException: {e}. Restarting listening process...")
                self.retry_count += 1
                time.sleep(2)  # Optional delay before retrying

            except Exception as e:
                print(f"Unhandled exception: {e}. Restarting listening process...")
                self.retry_count += 1
                time.sleep(2)

        if self.retry_count >= self.max_retries:
            print("Max retries reached. Could not establish connection with Deepgram.")


    def get_final_result(self):
        # print("Sending final result:", self.final_result)
        return self.final_result

# todo: implement saving