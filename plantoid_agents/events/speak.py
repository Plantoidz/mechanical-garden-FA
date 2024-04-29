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
# import pygame.mixer as mixer
import types

from utils.experiments.MultichannelRouter import Iterator, magicstream

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs, AsyncElevenLabs
from elevenlabs import stream, Voice, VoiceSettings, play

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

    def format_response_type(self, response: Any) -> Any:
        return self.stream_text(response) if isinstance(response, types.GeneratorType) else response

    # def play_background_music(self, loops=-1) -> None:

    #     # get the path to the background music
    #     background_music_path = os.getcwd()+"/media/ambient3.mp3"

    #     mixer.init()
    #     mixer.music.load(background_music_path)
    #     mixer.music.play(loops)

    # #todo: rename function and make this more general — cue sounds not just background music
    # def stop_background_music(self) -> None:

    #     if mixer.get_init() is not None:
    #         print('stop background music')
    #         mixer.music.stop()

    def get_voice_clone_files(self):

        # Define the directory path where you want to list the files
        directory_path = os.getcwd()+"/media/user_audio/temp"

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
        voice_files = [open(file_, 'rb') for file_ in voice_file_paths]
        print("Using voice files: ", voice_file_paths)

        if create_clone:
            
            print('Creating a clone of the user voice...')

            voice = client.voices.add(
                name="You",
                description="A clone of the user's voice",
                files=voice_files,
            )

            cloned_voice_id = voice.voice_id

            if voice_set_callback is not None:
                print("Cloned voice ID: ", cloned_voice_id)
                voice_set_callback(cloned_voice_id)


        else:
            print('Using the previously cloned voice...')

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

        # voice = client.clone(
        #     # api_key=os.getenv("ELEVENLABS_API_KEY"),
        #     name="You",
        #     description="A clone of the user's voice", # Optional
        #     files=voice_file_paths,
        # )

        return voice

    def stream_audio_response(
        self,
        response: str,
        voice_id: str,
        channel_id: str,
        callback: Any = None,
        use_multichannel: bool = True,
        use_streaming: bool = True,
    ) -> None:

        # print("use streaming = ", use_streaming)

        if(use_streaming):

            # generate audio stream   
            audio_stream = client.generate(
                text=self.stream_text(response),
                model="eleven_turbo_v2",
                voice=voice_id,
                stream=True
            )

            # stop background music callback
            if callback is not None:
                callback()
                    
            # stream audio
            # stream(audio_stream)
                
            if use_multichannel:
                print("\033[90mstreaming on channel",channel_id,"\033[0m\n")
                magicstream(audio_stream, channel_id)

            else:
                stream(audio_stream)
        
        else:
            audio = client.generate(
                text=response,
                model="eleven_turbo_v2",
                voice=voice_id,
                stream=False
            )
            #todo: implement magicplay
            play(audio)

    def speak(
        self,
        agents,
        agent,
        response: str,
        voice_id: str,
        channel_id: str,
        callback: Any = None,
        voice_set_callback: Any = None,
        clone_voice: bool = False,
        create_clone: bool = False,
        use_streaming: bool = True,

    ) -> None:

        # for a in agents:
        #     if(a.callback): a.callback("<asleep>")

        # if(agent.callback): agent.callback("<speaking>")


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
                use_streaming=use_streaming,
            )

        else:
            self.stream_audio_response(
                response,
                voice_id,
                channel_id,
                callback=callback,
                use_streaming=use_streaming,

            )
