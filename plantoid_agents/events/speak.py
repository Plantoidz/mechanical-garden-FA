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
from elevenlabs.client import ElevenLabs, AsyncElevenLabs
from elevenlabs import stream, Voice, VoiceSettings

# https://elevenlabs.io/docs/api-reference/edit-voice


# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

client = ElevenLabs(
  api_key=ELEVENLABS_API_KEY
)

# set_api_key(ELEVENLABS_API_KEY)

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
        audio_stream = client.generate(
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

    #todo: rename function and make this more general — cue sounds not just background music
    def stop_background_music(self) -> None:

        if pygame.mixer.get_init() is not None:
            print('stop background music')
            background.music.stop()

    def clone_voice(
        self,
        voice_set_callback: Any,
        cloned_voice_id: str = None,
        create_clone: bool = False
    ):

        voice_files = [os.getcwd()+"/media/user_audio/temp_reco.wav"]

        if create_clone:
            print('Creating a clone of the user voice...')
            voice = client.clone(
                # api_key=os.getenv("ELEVENLABS_API_KEY"),
                name="You",
                description="A clone of the user's voice", # Optional
                files=voice_files,
            )

            voice_set_callback(voice.voice_id)
            # TODO: use this to add progressive voice files to improve voice
            # client.voices.edit()

        else:
            print('Using the previously cloned voice...')
            voice = Voice(
                voice_id=cloned_voice_id, #'NE1ZIqHDl04rAu3fkYQH',
                settings=VoiceSettings(
                    stability=0.61,
                    similarity_boost=0.85,
                    style=0.0,
                    use_speaker_boost=True,
                )
            )

        return voice

    def speak(
        self,
        response: str,
        voice_id: str,
        callback: Any = None,
        voice_set_callback: Any = None,
        clone_voice: bool = False,
        create_clone: bool = False,

    ) -> None:

        if clone_voice:

            voice = self.clone_voice(
                create_clone=create_clone,
                cloned_voice_id=voice_id,
                voice_set_callback=voice_set_callback,
            )

            self.stream_audio_response(
                response,
                voice,
                callback=callback,
            )

        else:
            self.stream_audio_response(
                response,
                voice_id,
                callback=callback,
            )
