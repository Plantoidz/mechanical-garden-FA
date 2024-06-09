from multiprocessing import Queue, Event
from typing import Iterator
import logging
import asyncio

def magicstream_websocket(
    audio_stream: Iterator[bytes],
    instruct_queue: Queue,
    speech_queue: Queue,
    speech_event: Event,
    timeout: int = 30,
    esp_id: int = None,
):

    logging.info(f"MAGICSTREAM WEBSOCKET, AGENT ESP ID: {esp_id}")

    try:
        
        loop = asyncio.get_event_loop()
        
        for chunk in audio_stream:
            if chunk:
                
                loop.run_in_executor(None, speech_queue.put_nowait, (esp_id, chunk))
        #        logging.info(f"Queued audio stream chunk of size: {len(chunk)} bytes with ESP ID: {esp_id}")

        # Signal the end of the stream
        loop.run_in_executor(None, speech_queue.put, (esp_id, None))

        # instruct the ESP to playback 
        loop.run_in_executor(None, instruct_queue.put, (esp_id, "3"))

        # Wait for the playback termination message
        logging.info("Waiting for playback termination message from playback server.")

        if speech_event.wait(timeout):
            logging.info("Playback termination message received.")
        else:
            logging.warning(f"No playback termination message received within {timeout} seconds.")

        logging.info("Playback termination message received.")

    except Exception as e:
        print(f"An error occurred while queuing audio stream: {e}")

def magicstream_local_websocket(
    audio_stream: any,
    instruct_queue: Queue,
    speech_queue: Queue,
    speech_event: Event,
    timeout: int = 30,
    esp_id: int = None,
):

    logging.info(f"MAGICSTREAM WEBSOCKET, AGENT ESP ID: {esp_id}")

    def on_audio_chunk(chunk):
        if chunk is not None:
            # print("chunk len", len(chunk))
            loop.run_in_executor(None, speech_queue.put_nowait, (esp_id, chunk))  
    try:
        
        loop = asyncio.get_event_loop()

        audio_stream.play_async(
            on_audio_chunk=on_audio_chunk,
            muted=True,
        )

        loop.run_in_executor(None, speech_queue.put_nowait, (esp_id, None))                    
        loop.run_in_executor(None, instruct_queue.put_nowait, (esp_id, "3"))                    

        if speech_event.wait(timeout):
            print("Playback termination message received.")
        else:
            print(f"No playback termination message received within {timeout} seconds.")

    except Exception as e:
        print(f"An error occurred while queuing audio stream: {e}")
