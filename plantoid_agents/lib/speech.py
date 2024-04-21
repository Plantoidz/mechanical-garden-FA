#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr

import pyaudio
import wave
import audioop
import struct

from simpleaichat import AIChat
from whisper_mic.whisper_mic import WhisperMic
from elevenlabs import play, stream, save
from elevenlabs.client import ElevenLabs

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



from config.scripts.default_prompt_config import default_chat_completion_config, default_completion_config
from utils.util import load_config, str_to_bool



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



# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")


def get_chat_response(chat_personality, utterance):

    # TODO: assess performance of instantiation
    ai_chat = AIChat(system=chat_personality, api_key=OPENAI_API_KEY, model="gpt-4-1106-preview")

    response = ai_chat(utterance)
    print(f"I said: {response}")

    return response
    


