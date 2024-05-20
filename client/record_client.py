import pyaudio
import asyncio
import websockets
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

RATE = 16000
CHUNK = 1024
PORT = 8888

DEVICE_INDEX = None

async def record_microphone(stream):
    while True:
        try:
            data = stream.read(CHUNK)
            yield data
        except IOError as e:
            logging.error(f"Input overflowed: {e}")
            # await asyncio.sleep(0.1)  # Add a small delay to help buffer catch up
            continue


async def on_message(ws):
    try:
        while True:
            message = await ws.recv()
            logging.info(f"Received message: {message}")
            await asyncio.sleep(1)
    except websockets.ConnectionClosedOK:
        logging.info("Connection closed normally.")
    except websockets.ConnectionClosedError as e:
        logging.error(f"Connection closed with error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in on_message: {e}")

async def send_audio():
    p = pyaudio.PyAudio()
    stream = None
    
    try:
        # Obtain the index of available mic
        # mic_device_index = None
        # for i in range(p.get_device_count()):
        #     device_info = p.get_device_info_by_index(i)
        #     if device_info['maxInputChannels'] > 0:
        #         mic_device_index = i
        #         break

        # if mic_device_index is None:
        #     logging.error("No microphone found")
        #     return

        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK,
                        input_device_index=None)

        async with websockets.connect(f'ws://localhost:{PORT}') as ws:
            logging.info(f"Connected to ws://localhost:{PORT}")
            # message_task = asyncio.create_task(on_message(ws))
            
            try:
                async for data in record_microphone(stream):
                    await ws.send(data)
            except websockets.ConnectionClosed:
                logging.info("WebSocket connection closed")
            # finally:
            #     await message_task  # Ensure the on_message task is awaited and handled

    except websockets.ConnectionClosedError as e:
        logging.error(f"Connection closed with error: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        p.terminate()
        logging.info("Resources have been cleaned up.")

if __name__ == '__main__':
    asyncio.run(send_audio())
