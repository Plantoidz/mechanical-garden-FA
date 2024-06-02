import time
import pyaudio
import numpy as np
import asyncio
import websockets
import wave
import logging
import os
from dotenv import load_dotenv
from pydub import AudioSegment
from io import BytesIO
from faster_whisper import WhisperModel
from elevenlabs.client import ElevenLabs, AsyncElevenLabs
from elevenlabs import stream, Voice, VoiceSettings, play


# Define Ports
TRANSCRIBE_PORT = 8888
STREAM_PORT = 7777

# Load environment variables from .env file
load_dotenv()

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHUNK_SIZE = 1024
INIT = 0
FILE = "test.wav"
# agents = []  # where all agents encountered so far are stored

model = WhisperModel("small", compute_type="auto", device="cpu")
audio = pyaudio.PyAudio()
stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    output=True,
    frames_per_buffer=CHUNK_SIZE
)

client = ElevenLabs(
  api_key=ELEVENLABS_API_KEY
)

voice_id  = "K5W90fMZclFpp7zIpkCc"


def register_esp(esp_id, ws, esp_ws_queue):

    esp_ws_queue.put(esp_id)
    logging.info(f"Registering ESP id: {esp_id} with socket: {ws}")

def unregister_esp(esp_id, esp_ws_queue):
    logging.info(f"Unregistering ESP id: {esp_id}")
    # for i, a in enumerate(agents):
    #     if a["id"] == esp:
    #         agents.pop(i)
    #         break

async def save_and_transcribe(audio_data):
    timestamp = time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())
    logging.info(f"Processing audio data at {timestamp}")

    audio = AudioSegment.from_raw(BytesIO(audio_data), sample_width=2, frame_rate=16000, channels=2)
    mono_audio = audio.set_channels(1)
    resampled_audio = mono_audio.set_frame_rate(16000)

    # Export to in-memory bytes buffer
    buffer = BytesIO()
    resampled_audio.export(buffer, format="wav")
    buffer.seek(0)

    # Pass in-memory buffer to whisper model
    segments, info = model.transcribe(buffer, beam_size=5, language="en")
    # logging.info(f"Detected language '{info.language}' with probability {info.language_probability}")

    for segment in segments:
        logging.info("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

async def transcribe_audio(websocket, path, esp_ws_queue, listen_queue, listen_event):
    global INIT
    esp_id = await websocket.recv()
    logging.info(f"Found ESP with id: {esp_id}")
    register_esp(esp_id, websocket, esp_ws_queue)

    if not INIT:
        logging.info("INIT is unset, starting switch modes task.")
        asyncio.create_task(switch_modes(None))
        INIT = 1

    audio_data = bytearray()
    try:
        async for msg in websocket:
            audio_data.extend(msg)
            if len(audio_data) >= 32000 * 2 * 2:
                current_audio_data = audio_data.copy()
                audio_data = bytearray()
                asyncio.create_task(save_and_transcribe(current_audio_data))
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        unregister_esp(esp_id, esp_ws_queue)

async def send_stream_to_websocket(websocket, path, esp_ws_queue, speech_queue, speech_event):

    esp_id = int(await websocket.recv())
    logging.info(f"Welcome to {esp_id}")
    register_esp(esp_id, websocket, esp_ws_queue)

    await websocket.send(f"START_PLAYBACK: {esp_id}")
    
    loop = asyncio.get_event_loop()
    try:
        while True:
            agent_esp_id, chunk = await loop.run_in_executor(None, speech_queue.get)

            if chunk is None:
                break

            if agent_esp_id == esp_id:
                await websocket.send(chunk)

            else:
                await websocket.send("END_STREAM")
                break
            logging.info(f"Sent audio stream chunk of size: {len(chunk)} bytes")

            # else:
            #     logging.info(f"Skipping audio stream chunk for ESP: {agent_esp_id}")
            #     await websocket.send("END_STREAM")

        await websocket.send("END_STREAM")

        # Wait for the client's playback termination message
        termination_message = await websocket.recv()
        if termination_message == "PLAYBACK_COMPLETE":  # Adjust this condition as needed
            logging.info("Received playback termination message from client")
            speech_event.set()
            # Reset the event for the next session
            speech_event.clear()

    except Exception as e:
        logging.error(f"An error occurred while sending audio stream: {e}")

async def switch_modes(agents):
    global FILE
    logging.info("Switch mode activated")

    tasks = [
        {"esp": "3", "mode": 1, "arg": None},
    ]

    for task in tasks:
        logging.info(f"Processing task: esp={task['esp']} mode={task['mode']}")
        ws = None
        for a in agents:
            if a["id"] == task["esp"]:
                ws = a["ws"]
                logging.info(f"Found a match for {task['esp']} with socket: {ws}")
                break

        if ws is None:
            for a in agents:
                if a["ws"]:
                    ws = a["ws"]
                    logging.info(f"Fallback to ESP {a['id']}")
                    break

        MODE = task["mode"]
        FILE = task["arg"]
        await ws.send(str(MODE))
        await asyncio.sleep(7) #NOTE: mock

def run_websocket_server(queues, events):
    
    logging.info("Starting server")
    loop = asyncio.get_event_loop()
    
    speech_queue = queues["speech"]
    listen_queue = queues["listen"]
    esp_ws_queue = queues["esp_ws"]

    speech_event = events["speech"]
    listen_event = events["listen"]

    if speech_queue is not None:

        speech_stream = websockets.serve(lambda ws, path: send_stream_to_websocket(ws, path, esp_ws_queue, speech_queue, speech_event), '', STREAM_PORT, ping_interval=None)
        loop.run_until_complete(speech_stream)

    if listen_queue is not None:

        listen_stream = websockets.serve(lambda ws, path: transcribe_audio(ws, path, esp_ws_queue, listen_queue, listen_event), '', TRANSCRIBE_PORT, ping_interval=None)
        loop.run_until_complete(listen_stream)
    
        # loop.run_until_complete(websockets.serve(transcribe_audio, '', TRANSCRIBE_PORT, ping_interval=None))
        # loop.run_until_complete(websockets.serve(send_stream_to_websocket, '', STREAM_PORT, ping_interval=None))
    loop.run_forever()

if __name__ == '__main__':
    run_websocket_server()


# async def send_stream_to_websocket(websocket, path, queue):

#     esp_id = await websocket.recv()
#     logging.info(f"Welcome to {esp_id}")
#     register_esp(esp_id, websocket)
    
#     text = "Hello my name is plantoid i am a blockchain based life form"
    
#     # Generate the audio stream
#     audio_stream = client.generate(
#         text=text,
#         model="eleven_turbo_v2",
#         voice=voice_id,
#         stream=True
#     )

#     # time.sleep(5)

#     # Send the audio stream data over the websocket, this is an MP3
#     try:
#         for chunk in audio_stream:
#             if chunk:
#                 await websocket.send(chunk)
#                 logging.info(f"Sent audio stream chunk of size: {len(chunk)} bytes")


#     except Exception as e:
#         logging.error(f"An error occurred while sending audio stream: {e}")