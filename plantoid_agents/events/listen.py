from typing import Any, Dict, List, Type

import speech_recognition as sr

import pyaudio
import wave
import audioop
import struct
import random
import os
import sys
import time
import random
import requests
import numpy as np
import whisper
import torch
import threading
# import pygame.mixer as mixer

from playsound import playsound
from dotenv import load_dotenv
from elevenlabs import stream
from utils.util import load_config, str_to_bool
from ctypes import *
from contextlib import contextmanager
from collections import deque

from utils.config_util import read_services_config
from plantoid_agents.lib.DeepgramTranscription import DeepgramTranscription

# from whisper_mic.whisper_mic import WhisperMic

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# client = ElevenLabs(
#   api_key=ELEVENLABS_API_KEY
# )

# set_api_key(ELEVENLABS_API_KEY)


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

class Listen:
    """
    A template class for implementing listening behaviors in an interaction system.
    """

    def __init__(
        self,
        timeout: int = 15,
        silence_limit: int = 1,
        threshold: int = 500,
        record_seconds: int = 2,
        rate: int = 16000,
        chunk: int = 512,
        channels: int = 1,
        device_index: int = None,
    ) -> None:
        """
        Initializes a new instance of the Listen class.
        """

        services = read_services_config()

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = channels
        self.RATE = rate
        self.CHUNK = chunk
        self.SILENCE_LIMIT = silence_limit   # seconds of silence will stop the recording
        self.TIMEOUT = timeout
        self.RECORD_SECONDS = record_seconds #seconds to listen for environmental noise
        self.THRESHOLD = threshold
        self.device_index = device_index
        self.transcription = DeepgramTranscription(sample_rate=self.RATE, device_index=self.device_index)
        self.tts_model_type = services["speech_recognition_model"]

    #todo: revisit cue sounds and background music
    def play_speech_indicator(self) -> None:
            
        # get the path to the speech indicator sound
        speech_indicator_path = os.getcwd()+"/media/beep_start.wav"
        playsound(speech_indicator_path, block=False)

        # mixer.init()
        # mixer.music.load(speech_indicator_path)
        # mixer.music.play(loops=1)

    def play_speech_acknowledgement(self, voice_id: str) -> None:
        random_effect = random.choice([
            'oh', 'um', 'hrm', 'hrmmmmm',
            'okay', 'i see', 'right',
             'ah', 'mhm.', 'ooh', # 'oh, really?'
            'ahh', 'hmm', 
        ])

        file_path = os.path.join(os.getcwd(), "media/runtime_effects", f"{voice_id}_{random_effect}.mp3")
        
        # Check if the file exists before trying to play it
        if os.path.exists(file_path):
            print(f"\n\033[94m{random_effect}\033[0m")
            playsound(file_path, block=False)
            # mixer.init()
            # mixer.music.load(file_path)
            # mixer.music.play(loops=1)
        else:
            # Print a warning message if the file does not exist
            print("\033[90m\nThe specified audio effect file does not exist. Skipping playback.\033[0m")
    
    def compute_average(self, fragment, sample_width=2):
        """Compute the raw average of audio samples."""
        
        # Number of samples in the fragment
        num_samples = len(fragment) // sample_width

        # Unpack the audio samples
        if sample_width == 1:
            fmt = f"{num_samples}B"  # Unsigned byte
            samples = struct.unpack(fmt, fragment)
            # Convert to signed values in the range -128 to 127
            samples = [s - 128 for s in samples]
        elif sample_width == 2:
            fmt = f"{num_samples}h"  # Short
            samples = struct.unpack(fmt, fragment)
        else:
            raise ValueError("Unsupported sample width")
        
        # Compute the average
        avg = sum(samples) / num_samples
        return avg

    def compute_median(self, fragment, sample_width=2):
        """Compute the median of audio samples."""
        
        # Number of samples in the fragment
        num_samples = len(fragment) // sample_width

        # Unpack the audio samples
        if sample_width == 1:
            fmt = f"{num_samples}B"  # Unsigned byte
            samples = struct.unpack(fmt, fragment)
            # Convert to signed values in the range -128 to 127
            samples = [s - 128 for s in samples]
        elif sample_width == 2:
            fmt = f"{num_samples}h"  # Short
            samples = struct.unpack(fmt, fragment)
        else:
            raise ValueError("Unsupported sample width")

        # Compute the median
        sorted_samples = sorted(samples)
        mid = num_samples // 2
        if num_samples % 2 == 0:  # even number of samples
            median = (sorted_samples[mid - 1] + sorted_samples[mid]) / 2
        else:
            median = sorted_samples[mid]
        
        return median

    def adjust_sound_env(self, stream, device_bias=0): ## important in order to adjust the THRESHOLD based on environmental noise
        
        data = []
        noisy = []

        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)

            manual_average = abs(self.compute_average(data, sample_width=2))
            manual_median = abs(self.compute_median(data, sample_width=2))
            audioop_average = abs(audioop.avg(data, 2))

            # print("manual median", manual_median)
            # print("manual average", manual_average)
            # print("audioop average", audioop_average)
            # print("\n")

            noisy.append(audioop_average)
    
        # current_noise = sum(noisy) / len(noisy)
        current_noise = np.mean(noisy) 
        # current_noise = np.median(noisy)

        # add device bias
        current_noise = max(0, current_noise + device_bias)

        print("current noise = " + str(current_noise))

        return current_noise

    def return_noise_threshold(self, noisy, threshold_bias=0):

        THRESHOLD = 0

        multiplier = 1.5
        # ## range should be:  if noisy is 10 = 50; if noisy = 100 = 250;
        # if(noisy < 10): THRESHOLD = 50
        # if(noisy > 10 and noisy < 20): THRESHOLD = 100 + bias 
        # if(noisy > 20 and noisy < 30): THRESHOLD = 140 + bias
        # if(noisy > 30 and noisy < 40): THRESHOLD = 160 + bias
        # if(noisy > 40 and noisy < 50): THRESHOLD = 170 + bias
        # if(noisy > 50 and noisy < 60): THRESHOLD = 200 + bias
        # if(noisy > 60 and noisy < 70): THRESHOLD = 300 + bias
        # if(noisy > 70): THRESHOLD = 350 + bias

        noise_ranges = list(np.array([0, 10, 20, 30, 40, 50, 60, 70, float('inf')]) * multiplier)
        thresholds = list(np.array([50, 100, 140, 160, 170, 200, 300, 350] ))

        # Ensure that the length of noise_ranges is one more than the length of thresholds
        if len(noise_ranges) != len(thresholds) + 1:
            raise ValueError("noise_ranges should have one more element than thresholds")

        for i in range(len(noise_ranges) - 1):

            if noise_ranges[i] <= noisy < noise_ranges[i + 1]:

                return max(0, thresholds[i] + threshold_bias)
            
        return max(0,thresholds[-1] + threshold_bias)

    def listen_for_speech_manual(self, timeout_override: str = None): # @@@ remember to add acknowledgements afterwards

        config = load_config(os.getcwd()+'/configuration.toml')

        cfg = config['audio']

        # TEMP
        record_mode = 'fixed'

        use_timeout = self.TIMEOUT

        if timeout_override is not None:
            use_timeout = timeout_override

        print("Timeout override: ", timeout_override)
        print("Use timeout: ", use_timeout)

        # define the audio file path
        # TODO: pass as param
        audio_file_path = os.getcwd() + "/media/user_audio/temp/temp_reco.wav"

        # audio = pyaudio.PyAudio()

        with ignoreStderr():
            audio = pyaudio.PyAudio()

        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index = self.device_index,
            frames_per_buffer=self.CHUNK
        )
        
        print('quiet! checking noise threshold...')

        # noise_value = self.adjust_sound_env(stream, device_bias=cfg['device_bias'])
        # THRESHOLD = self.return_noise_threshold(noise_value, threshold_bias=cfg['threshold_bias'])
        THRESHOLD = self.THRESHOLD

        # print("THRESHOLD:", THRESHOLD)

        samples = []

        if record_mode == 'fixed':

            print('fixed mode - listening for speech...')

            # this is for a fixed amount of recording seconds
            for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                data = stream.read(self.CHUNK)
                samples.append(data)

            self.record_wav_file(samples, audio, audio_file_path)

        if record_mode == 'continuous':

            print('listening for speech...')

            chunks_per_second = self.RATE / self.CHUNK

            silence_buffer = deque(maxlen=int(self.SILENCE_LIMIT * chunks_per_second))
            samples_buffer = deque(maxlen=int(self.SILENCE_LIMIT * self.RATE))

            started = False

            ### this is for continuous recording, until silence is reached

            run = 1

            timing = None

            print('preparing to record...')

            while(run):

                data = stream.read(self.CHUNK, exception_on_overflow=True)
                # Process your data here
                # Example: calculate the average volume
                volume = audioop.rms(data, 2)  # Adjust according to the format

                silence_buffer.append(volume)

                if (True in [x > THRESHOLD for x in silence_buffer]):

                    if not started:
                        print ("recording started")
                        started = True
                        samples_buffer.clear()
                        timing = time.time()

                    samples.append(data)

                    # check for timeout
                    if(time.time() - timing > use_timeout):
                        print(">>> stopping recording because of timeout")
                        stream.stop_stream()

                        self.record_wav_file(samples, audio, audio_file_path)

                        #reset all vars
                        started = False
                        silence_buffer.clear()
                        samples = []

                        run = 0


                elif(started == True):   ### there was a long enough silence
                    print ("recording stopped")
                    stream.stop_stream()
                    
                    self.record_wav_file(samples, audio, audio_file_path)

                    #reset all vars
                    started = False
                    silence_buffer.clear()
                    samples = []

                    run = 0

        stream.close()
        audio.terminate()

        return audio_file_path

    def record_wav_file(self, data, audio, audio_file_path):

        print("saving audio file to: ", audio_file_path)

        with wave.open(audio_file_path, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(data))
            #wf.close()

    def listen_for_speech_google(self, timeout_override: int = 1):

        # def countdown():
        #     # Countdown timer to run concurrently
        #     for i in range(self.TIMEOUT, 0, -1):
        #         print(f"Time remaining: {i} seconds", end='\r', flush=True)
        #         time.sleep(1)

        # # Initialize recognizer
        r = sr.Recognizer()

        # Set the energy threshold
        r.energy_threshold = 500 #self.THRESHOLD  # Adjust this based on the ambient noise level
        r.dynamic_energy_threshold = False

        # Set the pause threshold
        r.pause_threshold = 3 #self.SILENCE_LIMIT  # Adjust this based on the desired pause length


        # # Start countdown in a separate thread
        # countdown_thread = threading.Thread(target=countdown)
        # countdown_thread.start()

        use_timeout = self.TIMEOUT

        if timeout_override is not None:
            use_timeout = timeout_override

        audio_file_path = os.getcwd() + "/media/user_audio/temp/temp_reco.wav"

        # Obtain audio from the microphone
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)  # Automatically adjusts the energy threshold
            print("\t\033[91mListening for speech...\033[0m")
            audio = r.listen(source, timeout=use_timeout)

        # Save the audio to a WAV file
        with open(audio_file_path, "wb") as f:
            f.write(audio.get_wav_data())

    def recognize_speech(self, filename):
        
        with sr.AudioFile(filename) as source:

            r = sr.Recognizer()
            r.energy_threshold = 150
            r.dynamic_energy_threshold = False

            audio = r.record(source)
            usertext = ""
            
            try:
                print("trying to recognize from ... " + filename)
                usertext = r.recognize_google(audio)

            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")

            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))

            return usertext
        

    # def listen_for_speech_whisper(self):

    #     with ignoreStderr():
    #         mic = WhisperMic()
    #         utterance = mic.listen()
    #         # print(f"I heard: {utterance}")

    #     return utterance
    
    def recognize_whisper(self):

        print("\t\033[91mRecognizing with Whisper...\033[0m")

        audio_file_path = os.getcwd() + "/media/user_audio/temp/temp_reco.wav"

        device=("cuda" if torch.cuda.is_available() else "cpu")
        model_root="~/.cache/whisper"
        model_name="base"

        audio_model = whisper.load_model(model_name, download_root=model_root).to(device)

        result = audio_model.transcribe(
            audio_file_path,
            # language='french',
            suppress_tokens="",
            fp16=False,
        )

        utterance = result["text"]

        return utterance

    def recognize_speech_whisper_manual(self, timeout_override: str = None):

        self.listen_for_speech_manual(timeout_override)
        utterance = self.recognize_whisper()


        return utterance
    
    def recognize_speech_whisper_google(self, timeout_override: str = None):
        try:
            self.listen_for_speech_google(timeout_override=timeout_override)
        except sr.exceptions.WaitTimeoutError:
            print("\t\033[91mTimeout reached. Stopping the recording...\033[0m")
            return ""

        utterance = self.recognize_whisper()
        return utterance
    
    def recognize_speech_deepgram(self, step: int = 0):

        self.transcription.reset()
        self.transcription.start_listening(step=step)
        utterance = self.transcription.get_final_result()

        # print("DEEPGRAM UTTERANCE:", utterance)

        return utterance
    
    def listen(self, characters, timeout_override: str = None, step: int = 0) -> Any:

        # print("TTS MODEL TYPE:", self.tts_model_type)
        for character in characters:
            if(character.callback): character.callback("<listening>")

        if self.tts_model_type == "google":
            return self.recognize_speech_whisper_google(timeout_override)
        
        if self.tts_model_type == "whisper":
            return self.recognize_speech_whisper_manual(timeout_override)

        if self.tts_model_type == "deepgram":
            return self.recognize_speech_deepgram(step=step)

    # def runtime_ack_sound(self):
    #     try:
    #         random_effect = random.choice([
    #     'oh', 'oh.', 'oh?', 'um', 'hrm', 'hrmmmmm', 'interesting!', 'okay', 'i see', 'right', 'really?', 'really.', 'oh, really?', 'ah', 'mhm.', 'ooh', 'ahh', 'hmm', 'huh.', 'huh!', 'huh??', 'kay.'])
    #         file_path = os.path.join(os.getcwd(), "media", "runtime_effects", f"{self.voice_id}_{random_effect}.mp3")
    #         playsound(file_path, block=False)
    #     except FileNotFoundError:
    #         print("\033[90m\nThis effect wasn't generated at runtime.\033[0m")