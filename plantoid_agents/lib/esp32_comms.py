from multiprocessing import Queue
from typing import Iterator
import logging
import asyncio

def magicstream_websocket(audio_stream: Iterator[bytes], speech_queue: Queue):

    # ws = websocket.WebSocket()

    # ws.connect(socket_addr)

    logging.info("MAGICSTREAM WEBSOCKET")
    # print("audio_stream: ", audio_stream)
    # print("speech_queue: ", speech_queue)

    # Put the audio stream data into the queue
    try:
        loop = asyncio.get_event_loop()
        for chunk in audio_stream:
            if chunk:
                loop.run_in_executor(None, speech_queue.put_nowait, chunk)
                logging.info(f"Queued audio stream chunk of size: {len(chunk)} bytes")

        # Signal the end of the stream
        loop.run_in_executor(None, speech_queue.put_nowait, None)

    except Exception as e:
        print(f"An error occurred while queuing audio stream: {e}")