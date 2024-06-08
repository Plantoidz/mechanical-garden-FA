import asyncio
import logging
import os
import time
from dotenv import load_dotenv
from pydub import AudioSegment
from io import BytesIO
from faster_whisper import WhisperModel
from elevenlabs.client import ElevenLabs

import websockets

# Define Ports
ORCHESTRATE_PORT = 8888
STREAM_PORT = 7777

# Load environment variables from .env file
load_dotenv()

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
print("eleven: " + ELEVENLABS_API_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CHUNK_SIZE = 1024
INIT = 0
FILE = "test.wav"
agents = []  # where all agents encountered so far are stored

model = WhisperModel("small", compute_type="auto", device="cpu")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

mictask = None
voice_id = "K5W90fMZclFpp7zIpkCc"

global wav_buffer
wav_buffer = b''

global PLAYBACK
PLAYBACK = None

def register_esp(esp, ws):
    logging.info(f"Registering agent id: {esp} with socket: {ws}")
    agents.append({"id": esp, "ws": ws})

def unregister_esp(esp):
    logging.info(f"Unregistering ESP {esp}")
    for i, a in enumerate(agents):
        if a["id"] == esp:
            agents.pop(i)
            break

async def orchestrate_instructions(websocket, path):
    global INIT
    esp_id = await websocket.recv()
    logging.info(f"Welcome to {esp_id}")
    register_esp(esp_id, websocket)

    if not INIT:
        logging.info("INIT is unset, starting switch modes task.")
        asyncio.create_task(switch_modes())
        INIT = 1

    try:
        async for msg in websocket:
            pass  # This is where orchestration logic will go, if needed.
    finally:
        unregister_esp(esp_id)

async def send_stream_to_websocket(websocket, path):
    global PLAYBACK
    print("new agent connected")
    
    if PLAYBACK == None:
        PLAYBACK = "Hello my name is plantoid I am a blockchain-based life form"
    
    # Generate the audio stream
    audio_stream = client.generate(
        text=PLAYBACK,
        model="eleven_turbo_v2",
        voice=voice_id,
        stream=True,
        output_format="pcm_16000"
    )

    try:
        for chunk in audio_stream:
            if chunk:
                await websocket.send(chunk)
                logging.info(f"Sent audio stream chunk of size: {len(chunk)} bytes")
        await websocket.send(b'')
    except Exception as e:
        logging.error(f"An error occurred while sending audio stream: {e}")

async def switch_modes():
    global FILE
    global PLAYBACK
    logging.info("Switch mode activated")

    tasks = [
        {"esp": "89", "mode": 3, "arg": "Hello I am alive !!"}
    ]

    await asyncio.sleep(1)  # Mock delay

    while True:
        await asyncio.sleep(3)
        for task in tasks:
            logging.info(f"Processing task: esp={task['esp']} mode={task['mode']}")
            ws = None  # ws is an internal websocket variable 
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
            print("sending MODE to ESP")
            await ws.send(str(MODE))
            await asyncio.sleep(5)  # Mock delay

def main():
    logging.info("Starting server")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(orchestrate_instructions, '', ORCHESTRATE_PORT, ping_interval=None))
    loop.run_until_complete(websockets.serve(send_stream_to_websocket, '', STREAM_PORT, ping_interval=None))
    loop.run_forever()

if __name__ == '__main__':
    main()
