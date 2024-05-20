import time
import pyaudio
import numpy as np
import asyncio
import websockets
import wave
import os

CHUNK_SIZE = 1024

audio = pyaudio.PyAudio()

stream = audio.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    output=True,
                    frames_per_buffer=CHUNK_SIZE)
# stupid comment


def record_wav(wf):
    CHUNK = 1024
    data = 1
    while data:
        data = wf.readframes(CHUNK)
        yield data




async def websocket_handler(websocket, path):

    asyncio.create_task(send(websocket))

    try:
        async for message in websocket:
            audio_data = np.frombuffer(message, dtype=np.int16)
            stream.write(audio_data.tobytes())

    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()



async def start_websocket_server():
    async with websockets.serve(websocket_handler, '', 8888, ping_interval=None):
        await asyncio.Future()  # Keep the server running


async def start_websocket_audio():
        async with websockets.serve(send_audio, '', 7777, ping_interval=None):
                await asyncio.Future()  # Keep the server running


async def send(websocket):
        while True:
                await asyncio.sleep(10)
                await websocket.send("msg")

async def send_audio(ws, path):

        wf = wave.open(os.getcwd()+"/websockets/test.wav", 'rb')

        generator = record_wav(wf);

        try:
                for data in generator:
                        await ws.send(data)
        finally:
                wf.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(websocket_handler, '', 8888, ping_interval=None))
    loop.run_until_complete(websockets.serve(send_audio, '', 7777, ping_interval=None))
    loop.run_forever()


if __name__ == '__main__':
    main()