from deepgram import DeepgramClient, Microphone, LiveTranscriptionEvents, LiveOptions
from dotenv import load_dotenv
import logging, verboselogs
import time
from ctypes import *
from contextlib import contextmanager
import os
import sys

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
    def __init__(self, sample_rate: int = 16000, device_index: int = None, timeout: int = 5):
        self.deepgram = DeepgramClient()
        self.is_finals = []
        self.utterance = ""
        self.transcription_complete = False  # New flag for completion
        self.sample_rate = sample_rate
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
                self.final_result = ' '.join(self.is_finals)
                print(f"\033[90m\tSpeech Final: {self.final_result}\033[0m")
                self.utterance = self.final_result
                self.transcription_complete = True  # Set completion flag
                #self.is_finals = []  # Reset for potential further use
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
        self.utterance = self.final_result
        # if len(self.is_finals) > 0:
        #     # self.utterance = ' '.join(self.is_finals)
        #     self.utterance = self.final_result
        #     print(f"Deepgram Utterance End: {self.utterance}")
        #     self.is_finals = []
        #     self.transcription_complete = True

    def on_close(self, *args, **kwargs):
        print(f"\033[91m\tDeepgram Connection Closed\033[0m")

    def on_error(self, *args, **kwargs):
        error = kwargs['error'] 
        print(f"Deepgram Handled Error: {error}")

    def on_unhandled(self, *args, **kwargs):
        unhandled = kwargs['unhandled'] 
        print(f"Deepgram Unhandled Websocket Message: {unhandled}")

    def start_listening(self, step: int = 0):
        self.reset()  # Reset state at the beginning of a listening session
        with ignoreStderr():

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
                channels=1,
                #why does this sample_rate need to be hard coded?
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
                endpointing=300
            )

            if connection.start(options) is False:
                print("Failed to connect to Deepgram")
                return

            microphone = Microphone(
                connection.send,
                # input_device_index=self.device_index,
                # rate=self.sample_rate,
            )

            microphone.start()

            start_time = time.time()  # Note the start time

            # Wait until the transcription is complete or 5 seconds have elapsed
            while not self.transcription_complete or (time.time() - start_time) < self.timeout:
                time.sleep(0.1)  # Sleep briefly to avoid busy waiting
                # Optionally, you can keep a debug print here:
                # print("Transcribing...")

            audio_file_path = os.getcwd() + "/media/user_audio/temp_reco_dg.wav"

            # microphone.finish(audio_file_path=audio_file_path)
            # this won't be necessary if deepgram API can return an mp3
            microphone.finish()
            connection.finish()

    def get_final_result(self):
        return self.utterance

# todo: implement saving