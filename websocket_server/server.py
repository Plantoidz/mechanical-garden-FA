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


def register_esp(esp_id, ws):
    global agents

    # esp_ws_queue.put(esp_id)
    agents.append({"id": esp_id, "ws": ws})
    logging.info(f"Registering ESP id: {esp_id} with socket: {ws}")


def unregister_esp(esp_id):
    global agents

    logging.info(f"Unregistering ESP id: {esp_id}")
    for i, a in enumerate(agents):
        if a["id"] == esp_id:
            agents.pop(i)
            break
        



# async def switch_modes(agents):
#     global FILE
#     global PLAYBACK
#     logging.info("Switch mode activated")

#     tasks = [
#         {"esp": "89", "mode": 3, "arg": "Hello I am alive !!"}
#     ]

#     while True:
#         for task in tasks:
#             logging.info(f"Processing task: esp={task['esp']} mode={task['mode']}")
#             ws = None
#             for a in agents:
#                 if a["id"] == task["esp"]:
#                     ws = a["ws"]
#                     logging.info(f"Found a match for {task['esp']} with socket: {ws}")
#                     break

#             if ws is None:
#                 for a in agents:
#                     if a["ws"]:
#                         ws = a["ws"]
#                         logging.info(f"Fallback to ESP {a['id']}")
#                         break

#             MODE = task["mode"]
#             PLAYBACK = task["arg"]
#             print("Sending mode: " + str(MODE))
#             await ws.send(str(MODE))
#             await asyncio.sleep(1)  # NOTE: mock


async def orchestrate_instructions(websocket, path, instruct_queue, speech_event):
    global INIT
    global agents

    esp_id = await websocket.recv()
    logging.info(f"Welcome to {esp_id}")
    register_esp(esp_id, websocket)
    
    closed = asyncio.ensure_future(websocket.wait_closed())
    closed.add_done_callback(lambda task: unregister_esp(esp_id))


    if not INIT:
        logging.info("INIT is unset, starting async task for instruction.")
        asyncio.create_task(check_for_instructions(instruct_queue, speech_event))
        INIT = 1
        

    try:
            async for msg in websocket:
                pass  # This is where orchestration logic will go, if needed.
    finally:
            unregister_esp(esp_id)
    
    
    # loop = asyncio.get_event_loop()

    # while True:
    #     agent_esp_id, instruction = await loop.run_in_executor(None, instruct_queue.get)
    #     print("SERVER FOUND INSTRUCTION FOR ["+ agent_esp_id+ "]of type = ", type(esp_id), " with instruction == ", instruction)
    #     print("Current socket ---------esp-id == ["+ esp_id+ "] of type = ", type(esp_id))

    #     if(agent_esp_id == esp_id):
    #         try:
    #             print("PLAYBACK .............................................")
    #             await websocket.send(instruction)
    #         except websockets.exceptions.ConnectionClosed:
    #             logging.warning(f"Connection closed for ESP id: {esp_id}")
    #             unregister_esp(esp_id, esp_ws_queue)
    #     else: ### not for you, put it back in the queue !
    #         print("not for me------------------------------ putting instructions back in the Queue")
    #         loop.run_in_executor(None, instruct_queue.put, (agent_esp_id, instruction))
            
    



def playback_disconnected(speech_event):
    print("SET END EVENT -------------------------------------------> client disconnected after end of palyback") 
    speech_event.set()
    speech_event.clear()


async def send_stream_to_websocket(websocket, path, speech_queue, speech_event):
    
    closed = asyncio.ensure_future(websocket.wait_closed())
    closed.add_done_callback(lambda task: playback_disconnected(speech_event))

    
    
    loop = asyncio.get_event_loop()
    
    try:
        while True:
            agent_esp_id, chunk = await loop.run_in_executor(None, speech_queue.get)

            if chunk is None:
                break
            
            await websocket.send(chunk)
            await asyncio.sleep(0.0001)


        #    logging.info(f"Sent audio stream chunk of size: {len(chunk)} bytes")

        await websocket.send(b'')
        
    except Exception as e:
        logging.error(f"An error occurred while sending audio stream: {e}")


# async def transcribe_audio(websocket, path, esp_ws_queue, listen_queue, listen_event):
#     pass


async def check_for_instructions(instruct_queue, speech_event):
    
    loop = asyncio.get_event_loop()

    while True:
        esp_id, task = await loop.run_in_executor(None, instruct_queue.get)
        print("SERVER FOUND INSTRUCTION FOR ["+ esp_id+ "]of type = ", type(esp_id), " with instruction == ", task)
        logging.info(f"Processing task: esp={esp_id} mode={task}")
        
        ws = None
        for a in agents:
            if a["id"] == esp_id:
                ws = a["ws"]
                logging.info(f"Found a match for {esp_id} with socket: {ws}")
                break

        if ws is None:
            for a in agents:
                if a["ws"]:
                    ws = a["ws"]
                    logging.info(f"Fallback to ESP {a['id']}")
                    break

        if ws:
            print("Sending instruction .............")
            try:
                print("PLAYBACK .............................................")
                await ws.send(task)
            except websockets.exceptions.ConnectionClosed:
                logging.warning(f"Connection closed for ESP id: {esp_id}")
                unregister_esp(esp_id)
                speech_event.set()
                speech_event.clear()
            except Exception as err:
                logging.warning("ERROR SENDING INSTRUCTION: ", err)
                unregister_esp(esp_id)
                speech_event.set()
                speech_event.clear()
        # else: ### not for you, put it back in the queue !
        #     print("not for me------------------------------ putting instructions back in the Queue")
        #     loop.run_in_executor(None, instruct_queue.put, (agent_esp_id, instruction))


def run_websocket_server(queues, events):
    logging.info("Starting server")
    loop = asyncio.get_event_loop()

    speech_queue = queues["speech"] ### this is used by the orchestrator to send the audio chunks to the server
    # listen_queue = queues["listen"]
    
    # this is can deleted I think
    # esp_ws_queue = queues["esp_ws"]  ### this is used by the server to register the ESP in the orchestrator

    speech_event = events["speech"]
    # listen_event = events["listen"]
    
    instruct_queue = queues["instruct"]

    orchestrate_stream = websockets.serve(lambda ws, path: orchestrate_instructions(ws, path, instruct_queue, speech_event), '', ORCHESTRATE_PORT, ping_interval=None)
    loop.run_until_complete(orchestrate_stream)
    
    

    # if speech_queue is not None:
    speech_stream = websockets.serve(lambda ws, path: send_stream_to_websocket(ws, path, speech_queue, speech_event), '', SPEECH_PORT, ping_interval=None)
    loop.run_until_complete(speech_stream)

    # if listen_queue is not None:
    #     listen_stream = websockets.serve(lambda ws, path: transcribe_audio(ws, path, esp_ws_queue, listen_queue, listen_event), '', LISTEN_PORT, ping_interval=None)
    #     loop.run_until_complete(listen_stream)


    loop.run_forever()


if __name__ == '__main__':
    run_websocket_server()

