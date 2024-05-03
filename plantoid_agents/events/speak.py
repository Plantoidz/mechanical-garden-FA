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
import audioop
import threading

from utils.config_util import read_services_config
# from utils.experiments.MultichannelRouter import Iterator, magicstream, setup_magicstream
from plantoid_agents.lib.MultichannelRouter import Iterator, magicstream, setup_magicstream
from plantoid_agents.lib.DeepgramTranscription import DeepgramTranscription

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs, AsyncElevenLabs
from elevenlabs import stream, Voice, VoiceSettings, play
from utils.util import str_to_bool

# https://elevenlabs.io/docs/api-reference/edit-voice


# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

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
        services = read_services_config()

        # Initialization code here (if necessary)
        self.elevenlabs_model_type = services["speech_synthesis_model"]
        self.use_interruption = str_to_bool(services["use_interruption"])
        self.use_multichannel = str_to_bool(services["use_multichannel"])

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
                }
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
    
    def trigger_stop_event(
        self,
        use_streaming: bool,
        stop_event: threading.Event,
        interruption_callback: Any,
    ):
        """Listen to the microphone and set the stop_event when noise is detected."""

        if use_streaming:
            # Initialize PyAudio
            p = pyaudio.PyAudio()

            # Open stream
            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK,
                    )

            try:
                while not stop_event.is_set():
                    # Read data from the microphone
                    data = stream.read(self.CHUNK)
                    # Check the sound level
                    # print(audioop.findmax(data, 2))
                    if audioop.rms(data, 2) > self.THRESHOLD:  # audioop.rms gives the root mean square of the chunk
                        print("\nAudio input detected. Stopping streaming.")
                        stop_event.set()  # Signal that the stop condition has been met
                        # TODO: impleemnt equivalent
                        #stop_mpv_processes()
                        if interruption_callback is not None:
                            interruption_callback(True, "Ben", "Test message.")  # Notify the rest of the application
                            # playsound(os.getcwd() + "/media/cleanse.mp3", block=False)
                        break
            finally:
                # Clean up the PyAudio stream and instance
                stream.stop_stream()
                stream.close()
                p.terminate()

                # Ensure the stop_event is set if it hasn't been already
                if not stop_event.is_set():
                    stop_event.set()
                    # if interruption_callback is not None:
                    #     interruption_callback(agent_interrupted=False)  # No interruption was detected

    def shadow_listener(
        self,
        agent: Any,
        use_streaming: bool,
        stop_event: threading.Event,
        audio_detected_event: threading.Event,
        interruption_callback: Any
    ):
        """Listen to the microphone and set the stop_event when noise is detected."""

        if self.use_interruption and use_streaming:

            transcription = DeepgramTranscription(sample_rate=self.RATE, device_index=self.device_index, timeout=2)
            transcription.reset()
            transcription.start_listening(step=None)
            utterance = transcription.get_final_result()
            print("Shadow Listener - Utterance: ", utterance)
            # time.sleep(5)
            audio_detected_event.set()
            stop_event.set()
            # TODO: impleemnt equivalent
            # stop_mpv_processes()

            if interruption_callback is not None:
                interruption_callback(True, agent.name, utterance)  # Notify the rest of the application
                # runtime_effect = self.select_random_runtime_effect(agent.get_voice_id())
                # # print("Runtime effect: ", runtime_effect)
                # playsound(runtime_effect, block=False)

    def select_random_runtime_effect(self, voice_id):
        """
        Selects a random file from the specified directory.
        """
        directory = os.getcwd() + "/media/runtime_effects"
        prefix = f"{voice_id}_"
        
        # List all files that start with the given voice ID
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.startswith(prefix)]
        
        # Check if there are any matching files
        if not files:
            return None  # Return None or raise an Exception if no matching files are found

        # Randomly select a file
        random_file = random.choice(files)
        return os.path.join(directory, random_file)


    def stream_audio_response(
        self,
        agent: Any,
        response: str,
        voice_id: str,
        channel_id: str,
        bg_callback: Any = None,
        interruption_callback: Any = None,
        # use_multichannel: bool = False,
        use_streaming: bool = True,
    ) -> None:

        stop_event = threading.Event()
        audio_detected_event = threading.Event()

        # trigger_thread = threading.Thread(
        #     target=self.trigger_stop_event,
        #     args=(use_streaming, stop_event, interruption_callback)
        # )
        shadow_listener_thread = threading.Thread(
            target=self.shadow_listener,
            args=(agent, use_streaming, stop_event, audio_detected_event, interruption_callback)
        )
        shadow_listener_thread.start()
        # trigger_thread.start()

        try:

            if use_streaming:

                # generate audio stream   
                audio_stream = client.generate(
                    text=self.stream_text(response),
                    model=self.elevenlabs_model_type,
                    voice=voice_id,
                    stream=True
                )

                # stop background music callback
                if bg_callback is not None:
                    bg_callback()
                    
                if self.use_multichannel:
                    print("\033[90mstreaming on channel",channel_id,"\033[0m\n")
                    magicstream(audio_stream, channel_id)

                else:
                    stream(audio_stream)
            
            else:
                audio = client.generate(
                    text=response,
                    model=self.elevenlabs_model_type,
                    voice=voice_id,
                    stream=False
                )
                #todo: implement magicplay
                play(audio)

        finally:
            stop_event.set()
            audio_detected_event.set()
            shadow_listener_thread.join()
            # trigger_thread.join()  # Ensure the interrupt thread is cleaned up properly

    def speak(
        self,
        agents,
        agent,
        response: str,
        voice_id: str,
        channel_id: str,
        bg_callback: Any = None,
        voice_set_callback: Any = None,
        clone_voice: bool = False,
        create_clone: bool = False,
        use_streaming: bool = True,

    ) -> None:
        if use_streaming:
            setup_magicstream()

        for a in agents:
            if(a.callback): a.callback("<asleep>")

        if(agent.callback): agent.callback("<speaking>")


        if clone_voice:

            voice = self.clone_voice(
                create_clone=create_clone,
                cloned_voice_id=voice_id,
                voice_set_callback=voice_set_callback,
            )

            self.stream_audio_response(
                agent,
                response,
                voice,
                channel_id,
                bg_callback=bg_callback,
                use_streaming=use_streaming,
            )

        else:
            self.stream_audio_response(
                agent,
                response,
                voice_id,
                channel_id,
                bg_callback=bg_callback,
                use_streaming=use_streaming,

            )
