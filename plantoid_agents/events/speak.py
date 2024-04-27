from typing import Any, Dict, List, Type
import pyaudio
import wave
# import audioop
import struct
import random
import os
import sys
import time
import requests
import pygame.mixer as mixer
import types

from utils.experiments.MultichannelRouter import Iterator, magicstream

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
        
    def stream_text(self, response_stream):

        if isinstance(response_stream, str):
            return response_stream

        for chunk in response_stream:
            if 'choices' in chunk and chunk['choices'][0].get('delta', {}).get('content'):
                delta = chunk.choices[0].delta
                text_chunk = delta.content
                yield text_chunk
                print(text_chunk, end='', flush=True)

    # def format_response_type(self, response: Any) -> Any:
    #     return self.stream_text(response) if isinstance(response, types.GeneratorType) else response

    def stream_audio_response(
        self,
        response: str,
        voice_id: str,
        channel_id: str,
        callback: Any = None
    ) -> None:

        # generate audio stream   
        audio_stream = client.generate(
            text=self.stream_text(response),
            model="eleven_multilingual_v2",
            voice=voice_id,
            stream=True
        )

        # stop background music callback
        if callback is not None:
            callback()
                
        # stream audio
        # stream(audio_stream)
        # todo: figure out how to pass the channel_id all the way through
        print("MAGIC STREAM WITH CHANNEL_ID == ", channel_id)
        magicstream(audio_stream, channel_id)

        # # Check if the response is a generator
        # if isinstance(response, types.GeneratorType):
        #     processed_text = stream_text_(response)
        # else:
        #     # If response is a string, directly pass the string
        #     processed_text = response

    # Additional methods can be added here as needed

    # def play_background_music(self, loops=-1) -> None:

    #     # get the path to the background music
    #     background_music_path = os.getcwd()+"/media/ambient3.mp3"

    #     pygame.mixer.init()
    #     pygame.mixer.music.load(background_music_path)
    #     pygame.mixer.music.play(loops)

    # #todo: rename function and make this more general — cue sounds not just background music
    def stop_background_music(self) -> None:

        if mixer.get_init() is not None:
            print('stop background music')
            mixer.music.stop()

    def get_voice_clone_files(self):

        # Define the directory path where you want to list the files
        directory_path = os.getcwd()+"/media/user_audio/temp_test"

        # Get a list of all files and directories in the specified path
        files_and_directories = os.listdir(directory_path)

        # If you only want files, you can filter out directories
        files_full_path = [os.path.join(directory_path, f) for f in files_and_directories if os.path.isfile(os.path.join(directory_path, f))]

        return files_full_path

    def clone_voice(
        self,
        voice_set_callback: Any,
        cloned_voice_id: str = None,
        create_clone: bool = False
    ):

        voice_file_paths = self.get_voice_clone_files() #[os.getcwd()+"/media/user_audio/temp_reco.wav"]

        if create_clone:
            print('Creating a clone of the user voice...')
            voice = client.clone(
                # api_key=os.getenv("ELEVENLABS_API_KEY"),
                name="You",
                description="A clone of the user's voice", # Optional
                files=voice_file_paths,
            )

            if voice_set_callback is not None:
                voice_set_callback(voice.voice_id)


        else:
            print('Using the previously cloned voice...')

            try:

                print("Using voice files: ", voice_file_paths)
                voice_files = [open(file_, 'rb') for file_ in voice_file_paths]

                # TODO: use this to add progressive voice files to improve voice
                client.voices.edit(
                    name="You",
                    description="A clone of the user's voice",
                    voice_id=cloned_voice_id,
                    files=voice_files,
                )

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

            except Exception as e:
                print("Error: ", e)
                


    def speak(
        self,
        response: str,
        voice_id: str,
        channel_id: str,
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
                channel_id,
                callback=callback,
            )

        else:
            self.stream_audio_response(
                response,
                voice_id,
                channel_id,
                callback=callback,
            )
