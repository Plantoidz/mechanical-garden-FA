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
# from faster_whisper import WhisperModel
# from elevenlabs.client import ElevenLabs, AsyncElevenLabs
# from elevenlabs import stream, Voice, VoiceSettings, play


# Define Ports
ORCHESTRATE_PORT = 8888
SPEECH_PORT = 7777
LISTEN_PORT = 6666

# Load environment variables from .env file
load_dotenv()

# ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHUNK_SIZE = 1024
INIT = 0
FILE = "test.wav"
PLAYBACK = None

# NOTE: TEMP - local agents
agents = []  # where all agents encountered so far are stored


def register_esp(esp_id, ws, esp_ws_queue):
    global agents

    esp_ws_queue.put(esp_id)
    agents.append({"id": esp_id, "ws": ws})
    logging.info(f"Registering ESP id: {esp_id} with socket: {ws}")


def unregister_esp(esp_id, esp_ws_queue):
    global agents

    logging.info(f"Unregistering ESP id: {esp_id}")
    for i, a in enumerate(agents):
        if a["id"] == esp_id:
            agents.pop(i)
            break


async def switch_modes(agents):
    global FILE
    global PLAYBACK
    logging.info("Switch mode activated")

    tasks = [
        {"esp": "89", "mode": 3, "arg": "Hello I am alive !!"}
    ]

    while True:
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
            PLAYBACK = task["arg"]
            print("Sending mode: " + str(MODE))
            await ws.send(str(MODE))
            await asyncio.sleep(10)  # NOTE: mock


async def orchestrate_instructions(websocket, path, esp_ws_queue):
    global INIT
    global agents

    esp_id = await websocket.recv()
    logging.info(f"Welcome to {esp_id}")
    register_esp(esp_id, websocket, esp_ws_queue)

    if not INIT:
        logging.info("INIT is unset, starting switch modes task.")
        asyncio.create_task(switch_modes(agents))
        INIT = 1

    try:
        async for msg in websocket:
            await asyncio.sleep(1)  # Mock delay
            pass  # This is where orchestration logic will go, if needed.
    except websockets.ConnectionClosed:
        logging.warning(f"Connection closed for ESP id: {esp_id}")
    finally:
        unregister_esp(esp_id, esp_ws_queue)

async def send_stream_to_websocket(websocket, path, esp_ws_queue, speech_queue, speech_event):
    loop = asyncio.get_event_loop()
    try:
        while True:
            agent_esp_id, chunk = await loop.run_in_executor(None, speech_queue.get)

            if chunk is None:
                break

            await websocket.send(chunk)

            logging.info(f"Sent audio stream chunk of size: {len(chunk)} bytes")

        await websocket.send(b'')
        await asyncio.sleep(10)  # Mock delay

        print("SET END EVENT")
        speech_event.set()
        speech_event.clear()

    except Exception as e:
        logging.error(f"An error occurred while sending audio stream: {e}")

async def transcribe_audio(websocket, path, esp_ws_queue, listen_queue, listen_event):
    pass

def run_websocket_server(queues, events):
    logging.info("Starting server")
    loop = asyncio.get_event_loop()

    speech_queue = queues["speech"]
    listen_queue = queues["listen"]
    esp_ws_queue = queues["esp_ws"]

    speech_event = events["speech"]
    listen_event = events["listen"]

    orchestrate_stream = websockets.serve(lambda ws, path: orchestrate_instructions(ws, path, esp_ws_queue), '', ORCHESTRATE_PORT, ping_interval=None)
    loop.run_until_complete(orchestrate_stream)

    if speech_queue is not None:
        speech_stream = websockets.serve(lambda ws, path: send_stream_to_websocket(ws, path, esp_ws_queue, speech_queue, speech_event), '', SPEECH_PORT, ping_interval=None)
        loop.run_until_complete(speech_stream)

    if listen_queue is not None:
        listen_stream = websockets.serve(lambda ws, path: transcribe_audio(ws, path, esp_ws_queue, listen_queue, listen_event), '', LISTEN_PORT, ping_interval=None)
        loop.run_until_complete(listen_stream)

    loop.run_forever()


if __name__ == '__main__':
    run_websocket_server()

