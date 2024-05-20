import asyncio
import websockets
import wave
import logging
import pyaudio
import numpy as np
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define the server's ports as variables
PORT_AUDIO_STREAM = 7777
PORT_PLAYBACK = 8888

CHUNK = 1024
RATE = 44100

# Initialize PyAudio for playback in bi-directional communication if enabled
audio = None
stream = None

async def read_wav_file(wf):
    """
    Asynchronously read chunks of data from a WAV file.
    """
    while True:
        data = wf.readframes(CHUNK)
        if not data:
            break
        yield data

async def send_audio_to_stream(websocket, path):
    """
    Send audio data from a WAV file to the connected WebSocket client.
    """
    wf = wave.open(os.getcwd()+"/media/test.wav", 'rb')
    logging.info("Client connected, streaming audio from file.")
    try:
        async for data in read_wav_file(wf):
            await websocket.send(data)
    except websockets.ConnectionClosed:
        logging.info("Connection closed by client.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        wf.close()
        logging.info("Audio file closed.")

# async def send_periodic_message(websocket):
#     """
#     Send periodic messages to the client.
#     """
#     while True:
#         await asyncio.sleep(10)
#         await websocket.send("msg")

async def send_audio_to_stream_with_message(websocket, path):
    """
    Handle WebSocket connections for streaming audio from a file.
    """
    await asyncio.gather(
        send_audio_to_stream(websocket, path),
        # send_periodic_message(websocket)
    )

async def play_audio_from_stream(websocket, path):
    """
    Handle WebSocket connections for sending and receiving audio data.
    """
    # asyncio.create_task(send_periodic_message(websocket))
    try:

        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=RATE,
                            output=True,
                            frames_per_buffer=CHUNK)
    
        async for message in websocket:
            audio_data = np.frombuffer(message, dtype=np.int16)
            print(("audio_data", audio_data))
            stream.write(audio_data.tobytes())
            
    except websockets.ConnectionClosed:
        logging.info("Connection closed by client.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.info("Stopping and closing audio stream.")
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if audio is not None:
            audio.terminate()

async def start_websocket_servers():
    """
    Start the WebSocket servers and serve clients on different ports.
    """
    tasks = []

    ws_audio_stream = websockets.serve(
        send_audio_to_stream_with_message,
        '',
        PORT_AUDIO_STREAM,
        ping_interval=None
    )
    tasks.append(ws_audio_stream)
    logging.info(f"Audio stream server started on ws://localhost:{PORT_AUDIO_STREAM}")

    ws_playback = websockets.serve(
        play_audio_from_stream,
        '',
        PORT_PLAYBACK,
        ping_interval=None
    )
    tasks.append(ws_playback)
    logging.info(f"Playback server started on ws://localhost:{PORT_PLAYBACK}")

    await asyncio.gather(*tasks)
    await asyncio.Future()  # Keep the servers running

def run_websocket_server():
    try:
        asyncio.run(start_websocket_servers())
    except Exception as e:
        logging.error(f"An error occurred in the main loop: {e}")
    finally:
        # Ensure resources are cleaned up if the bi-directional server was enabled
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if audio is not None:
            audio.terminate()

if __name__ == '__main__':
    run_websocket_server()
