from typing import Any, Dict, List, Type

import pyaudio
import wave
import audioop
import struct
import random
import os
import sys
import time
import requests
import pygame


from dotenv import load_dotenv
from elevenlabs import generate, stream, set_api_key

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

set_api_key(ELEVENLABS_API_KEY)

class Speak:
    """
    A template class for implementing speaking behaviors in an interaction system.
    """

    def __init__(self):
        """
        Initializes a new instance of the Speak class.
        """
        # Initialization code here (if necessary)
        pass

    def get_text_to_speech_response(self, text, eleven_voice_id, callback=None):

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
        
    def stream_audio_response(self, response: str, voice_id: str, callback: Any = None) -> None:

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

    # Additional methods can be added here as needed

    def play_background_music(self, loops=-1) -> None:

        # get the path to the background music
        background_music_path = os.getcwd()+"/media/ambient3.mp3"

        pygame.mixer.init()
        pygame.mixer.music.load(background_music_path)
        pygame.mixer.music.play(loops)

    def stop_background_music(self) -> None:
        print('stop background music')
        pygame.mixer.music.stop()

    def speak(self, response: str, voice_id: str, callback: Any = None) -> None:

        self.stream_audio_response(
            response,
            voice_id,
            callback=callback,
        )
