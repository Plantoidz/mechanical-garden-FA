#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr

import pyaudio
import wave
import audioop
import struct

from simpleaichat import AIChat
from whisper_mic.whisper_mic import WhisperMic
from elevenlabs import generate, stream, set_api_key

import numpy as np

from collections import deque

from playsound import playsound

from dotenv import load_dotenv

import openai
import requests

import random
import os
import sys
import time

from ctypes import *
from contextlib import contextmanager

from config.scripts.default_prompt_config import default_chat_completion_config, default_completion_config
from utils.util import load_config, str_to_bool

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

# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100
# CHUNK = 512
# RECORD_SECONDS = 2 #seconds to listen for environmental noise
# AUDIO_FILE = "/tmp/temp_reco.wav"
# device_index = 6

# #define the silence threshold
# # THRESHOLD = 250     # Raspberry uses 150
# SILENCE_LIMIT = 4   # seconds of silence will stop the recording

# TIMEOUT = 15

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512
SILENCE_LIMIT = 3   # seconds of silence will stop the recording
TIMEOUT = 7#15
RECORD_SECONDS = 2 #seconds to listen for environmental noise
THRESHOLD = 150

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

set_api_key(ELEVENLABS_API_KEY)


def GPTmagic(prompt, call_type='chat_completion'): 

    # allowable kwargs
    allowable_call_types = ['chat_completion', 'completion']

    assert call_type in allowable_call_types, "The provided call type is not implemented"

    if call_type == 'chat_completion':

        # Prepare the GPT magic
        config = default_chat_completion_config(model="gpt-4")

        # Generate the response from the GPT model
        response = openai.ChatCompletion.create(messages=[{
            "role": "user",
            "content": prompt,
        }], **config)

        messages = response.choices[0].message.content
        print('gpt response:', messages)

        return messages
    
    if call_type == 'completion':
        # # The GPT-3.5 model ID you want to use
        # model_id = "text-davinci-003"

        # # The maximum number of tokens to generate in the response
        # max_tokens = 1024

        config = default_completion_config()

        # Generate the response from the GPT-3.5 model
        response = openai.Completion.create(
            prompt=prompt,
            **config,
        )

        return response


def get_text_to_speech_response(text, eleven_voice_id, callback=None):

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
    }

    #eleven_voice_id = '21m00Tcm4TlvDq8ikWAM' # Rachel
    url = "https://api.elevenlabs.io/v2/text-to-speech/"+eleven_voice_id

    # Request TTS from remote API
    response = requests.post(
        url,
        json={
            "text": text,
            "voice_settings": {
                "stability": 0,
                "similarity_boost": 0
            },
        },
        headers=headers,
    )

    if response.status_code == 200:
        # Save remote TTS output to a local audio file with an epoch timestamp

        print('elevenlabs response received')

        if callback is not None:
            callback()
            
        filename = f"/tmp/tonyspeak.mp3"
        with open(filename, "wb") as f:
            f.write(response.content)
        
        # playsound(filename)
        return filename
    
    else:

        status = response.json()['detail']['status']
        message = response.json()['detail']['message']

        raise Exception("Error: " + str(status) + ": "+ str(message))

def compute_average(fragment, sample_width=2):
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

def compute_median(fragment, sample_width=2):
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

def adjust_sound_env(stream, device_bias=0): ## important in order to adjust the THRESHOLD based on environmental noise
    
    data = []
    noisy = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)

        manual_average = abs(compute_average(data, sample_width=2))
        manual_median = abs(compute_median(data, sample_width=2))
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


def return_noise_threshold(noisy, threshold_bias=0):

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

def listen_for_speech(): # @@@ remember to add acknowledgements afterwards

    config = load_config(os.getcwd()+'/configuration.toml')

    cfg = config['audio']

    # TEMP
    record_mode = 'continuous'

    # define the audio file path
    # TODO: pass as param
    audio_file_path = os.getcwd() + "/tmp/temp_reco.wav"

    # audio = pyaudio.PyAudio()

    with ignoreStderr():
        audio = pyaudio.PyAudio()

    stream = audio.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                # input_device_index = device_index,
                frames_per_buffer=CHUNK)
    
    print('quiet! checking noise threshold...')

    noise_value = adjust_sound_env(stream, device_bias=cfg['device_bias'])
    THRESHOLD = return_noise_threshold(noise_value, threshold_bias=cfg['threshold_bias'])

    print("THRESHOLD:", THRESHOLD)

    samples = []

    if record_mode == 'fixed':

       # this is for a fixed amount of recording seconds
       for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
           data = stream.read(CHUNK)
           samples.append(data)

    if record_mode == 'continuous':

        print('listening for speech...')

        chunks_per_second = RATE / CHUNK

        silence_buffer = deque(maxlen=int(SILENCE_LIMIT * chunks_per_second))
        samples_buffer = deque(maxlen=int(SILENCE_LIMIT * RATE))

        started = False

        ### this is for continuous recording, until silence is reached

        run = 1

        timing = None

        print('preparing to record...')

        while(run):

            data = stream.read(CHUNK)
            silence_buffer.append(abs(audioop.avg(data, 2)))

            samples_buffer.extend(data)

            if (True in [x > THRESHOLD for x in silence_buffer]):

                if not started:
                    print ("recording started")
                    started = True
                    samples_buffer.clear()
                    timing = time.time()

                samples.append(data)

                # check for timeout
                if(time.time() - timing > TIMEOUT):
                    print(">>> stopping recording because of timeout")
                    stream.stop_stream()

                    record_wav_file(samples, audio, audio_file_path)

                    #reset all vars
                    started = False
                    silence_buffer.clear()
                    samples = []

                    run = 0


            elif(started == True):   ### there was a long enough silence
                print ("recording stopped")
                stream.stop_stream()
                
                record_wav_file(samples, audio, audio_file_path)

                #reset all vars
                started = False
                silence_buffer.clear()
                samples = []

                run = 0

    stream.close()
    audio.terminate()

    return audio_file_path

def record_wav_file(data, audio, audio_file_path):

    with wave.open(audio_file_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(data))
        #wf.close()


def recognize_speech(filename):
    

    with sr.AudioFile(filename) as source:

        r = sr.Recognizer()
        r.energy_threshold = 50
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
    

def listen_for_speech_whisper():

    with ignoreStderr():
        mic = WhisperMic()
        utterance = mic.listen()
        # print(f"I heard: {utterance}")

    return utterance
    
def get_chat_response(chat_personality, utterance):

    # TODO: assess performance of instantiation
    ai_chat = AIChat(system=chat_personality, api_key=OPENAI_API_KEY, model="gpt-4-1106-preview")

    response = ai_chat(utterance)
    print(f"I said: {response}")

    return response
    
def stream_audio_response(response, voice_id, callback=None):

    # generate audio stream   
    audio_stream = generate(
        text=f"{response}",
        model="eleven_turbo_v2",
        voice=voice_id,
        stream=True
    )

    # stop background music callback
    if callback is not None:
        callback()
            
    # stream audio
    stream(audio_stream)

