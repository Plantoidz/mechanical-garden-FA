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

    # ws = websocket.WebSocket()

    # ws.connect(socket_addr)

    logging.info(f"MAGICSTREAM WEBSOCKET, AGENT ESP ID: {esp_id}")
    # print("audio_stream: ", audio_stream)
    # print("speech_queue: ", speech_queue)
        
                    

    # Put the audio stream data into the queue
    try:
        

        loop = asyncio.get_event_loop()
        
        # loop.run_in_executor(None, instruct_queue.put_nowait, (esp_id, "3"))

        
        for chunk in audio_stream:
            if chunk:
                
                loop.run_in_executor(None, speech_queue.put_nowait, (esp_id, chunk))
        #        logging.info(f"Queued audio stream chunk of size: {len(chunk)} bytes with ESP ID: {esp_id}")

        # Signal the end of the stream
        loop.run_in_executor(None, speech_queue.put, (esp_id, None))

        loop.run_in_executor(None, instruct_queue.put, (esp_id, "3"))

   
  


        # Wait for the playback termination message
        logging.info("Waiting for playback termination message from client.")

        if speech_event.wait(timeout):
            logging.info("Playback termination message received.")
        else:
            logging.warning(f"No playback termination message received within {timeout} seconds.")

        logging.info("Playback termination message received.")

    except Exception as e:
        print(f"An error occurred while queuing audio stream: {e}")