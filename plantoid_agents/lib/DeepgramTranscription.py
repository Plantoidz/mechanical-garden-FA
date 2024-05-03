from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone
from dotenv import load_dotenv
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
    def __init__(self, sample_rate: int = 48000, device_index: int = None, channels: int = 1, timeout: int = 5):
        self.deepgram = DeepgramClient()
        self.is_finals = []
        self.final_result = ""
        self.transcription_complete = False  # New flag for completion
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.timeout = timeout  # Timeout in seconds

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
            else:
                print(f"\033[90m\tAlmost Final: {sentence}\033[0m")
        else:
            print(f"\033[90m\tInterim Results: {sentence}\033[0m")

    def on_metadata(self, *args, **kwargs):
        metadata = kwargs['metadata'] 
        print(f"Deepgram Metadata: {metadata}")

    def on_speech_started(self, *args, **kwargs):
        print(f"\033[91m\tDeepgram is listening...\033[0m")

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

        # print("Start listening deepgram...")
        # print("sample rate: ", self.sample_rate)
        # print("device index: ", self.device_index)        
        # with ignoreStderr():

        connection = self.deepgram.listen.live.v("1")
        connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
        # connection.on(LiveTranscriptionEvents.Metadata, self.on_metadata)
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

        if connection.start(options) is False:
            print("Failed to connect to Deepgram")
            return

        microphone = ModifiedMicrophone(
            connection.send,
            input_device_index=self.device_index,
            rate=self.sample_rate,
            channels=self.channels,
        )

        # microphone = Microphone(
        #     connection.send,
        #     rate=self.sample_rate,
        #     # input_device_index=self.device_index,
        # )

        microphone.start()

        start_time = time.time()  # Note the start time

        # time.sleep(5)

        # Wait until the transcription is complete or 5 seconds have elapsed
        while not self.transcription_complete or (time.time() - start_time) < self.timeout:
            time.sleep(0.1)  # Sleep briefly to avoid busy waiting
            # Optionally, you can keep a debug print here:
            # print("Transcribing...")

        # Define the directory path
        directory = os.path.join(os.getcwd(), "media/user_audio/temp")

        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Define the audio file path within the newly ensured directory
        audio_file_path = os.path.join(directory, f"temp_reco_dg_{str(step)}.wav")

        microphone.finish(audio_file_path=audio_file_path)
        # microphone.finish()
        connection.finish()
        
        #TODO: cue sounds based on pre-generated runtime_effects
        #TODO: should this be a callback to listen.py?
        # try:
        #     random_effect = random.choice([
        #         'oh', 'oh.', 'oh?', 'um', 'hrm', 'hrmmmmm', 'interesting!', 'okay', 'i see', 'right', 'really?', 'really.', 'oh, really?', 'ah', 'mhm.', 'ooh', 'ahh', 'hmm', 'huh.', 'huh!', 'huh??', 'kay.'
        #     ])

        #     file_path = os.path.join(os.getcwd(), "media", "runtime_effects", f"wyZnrAs18zdIj8UgFSV8_{random_effect}.mp3")
        #     playsound(file_path, block=False)
        # # TODO: don't crash if the file isn't there
        # except FileNotFoundError:
        #     print("\033[90m\nThis effect wasn't generated at runtime.\033[0m")

    def get_final_result(self):
        # print("Sending final result:", self.final_result)
        return self.final_result

# todo: implement saving