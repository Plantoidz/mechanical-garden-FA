from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone
from dotenv import load_dotenv
import logging, verboselogs
import time
from ctypes import *
from contextlib import contextmanager
import os
import sys

from microphone import ModifiedMicrophone

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
    def __init__(self, sample_rate: int = 48000, device_index: int = 0, timeout: int = 5):
        self.deepgram = DeepgramClient()
        self.is_finals = []
        self.utterance = ""
        self.transcription_complete = False  # New flag for completion
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.timeout = timeout  # Timeout in seconds
        
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
                utterance_ = ' '.join(self.is_finals)
                print(f"Speech Final: {utterance_}")

                # NOTE: moved to on_utterance_end event
                # self.transcription_complete = True  # Set completion flag
                # self.is_finals = []
            else:
                print(f"Is Final: {sentence}")
        else:
            print(f"Interim Results: {sentence}")

    def on_metadata(self, *args, **kwargs):
        metadata = kwargs['metadata'] 
        print(f"Deepgram Metadata: {metadata}")

    def on_speech_started(self, *args, **kwargs):
        print(f"Deepgram Speech Started")

    def on_utterance_end(self, *args, **kwargs):
        if len(self.is_finals) > 0:
            self.utterance = ' '.join(self.is_finals)
            print(f"Deepgram Utterance End: {self.utterance}")
            self.is_finals = []
            self.transcription_complete = True

    def on_close(self, *args, **kwargs):
        print(f"Deepgram Connection Closed")
        if len(self.is_finals) > 0:
            self.utterance = ' '.join(self.is_finals)
            print(f"Deepgram Utterance End: {self.utterance}")
            self.is_finals = []
            self.transcription_complete = True

    def on_error(self, *args, **kwargs):
        # error = kwargs['error'] 
        print(f"Deepgram Handled Error: {args} {kwargs}")

    def on_unhandled(self, *args, **kwargs):
        unhandled = kwargs['unhandled'] 
        print(f"Deepgram Unhandled Websocket Message: {unhandled}")

    def start_listening(self):

        print("Start listening deepgram...")
        print("sample rate: ", self.sample_rate)
        print("device index: ", self.device_index)

        
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
            channels=1,
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
            # input_device_index=self.device_index,
            rate=self.sample_rate,
        )

        # microphone = Microphone(
        #     connection.send,
        #     rate=self.sample_rate,
        #     # input_device_index=self.device_index,
        # )

        microphone.start()

        start_time = time.time()  # Note the start time

        time.sleep(5)

        # # Wait until the transcription is complete or 5 seconds have elapsed
        # while not self.transcription_complete or (time.time() - start_time) < self.timeout:
        #     time.sleep(0.1)  # Sleep briefly to avoid busy waiting
        #     # Optionally, you can keep a debug print here:
        #     # print("Transcribing...")

        audio_file_path = os.getcwd() + "/media/user_audio/temp_reco_dg.wav"

        microphone.finish(audio_file_path=audio_file_path)
        # microphone.finish()
        connection.finish()

        print("Finished")


    def get_final_result(self):
        return self.utterance

# todo: implement saving