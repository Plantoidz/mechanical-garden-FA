from multiprocessing import Queue, Event
from typing import Iterator
import logging
import asyncio
from pydub import AudioSegment
from io import BytesIO
import pyaudio

def convert_audio_chunk(chunk: bytes, src_format: int, src_channels: int, src_rate: int, dst_format: int, dst_channels: int, dst_rate: int) -> bytes:
    # Create an AudioSegment from the source chunk
    audio_segment = AudioSegment(
        data=chunk,
        sample_width=pyaudio.get_sample_size(src_format),
        frame_rate=src_rate,
        channels=src_channels
    )

    # Convert to the target format
    audio_segment = audio_segment.set_frame_rate(dst_rate)
    audio_segment = audio_segment.set_channels(dst_channels)
    audio_segment = audio_segment.set_sample_width(pyaudio.get_sample_size(dst_format))

    # Export to bytes
    buffer = BytesIO()
    audio_segment.export(buffer, format="raw")
    return buffer.getvalue()

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

    loop = asyncio.get_event_loop()

    def on_audio_chunk(chunk):
        if chunk is not None:
            # print("chunk len", len(chunk))

                # Example usage
            src_format = pyaudio.paFloat32
            src_channels = 1
            src_rate = 16000
            dst_format = pyaudio.paInt16
            dst_channels = 1
            dst_rate = 16000

            # Assume `audio_chunk` is a chunk of audio in the source format
            chunk = convert_audio_chunk(chunk, src_format, src_channels, src_rate, dst_format, dst_channels, dst_rate)
            loop.run_in_executor(None, speech_queue.put_nowait, (esp_id, chunk))  
    try:
        # loop.run_in_executor(None, instruct_queue.put_nowait, (esp_id, "3"))                    

        audio_stream.play(
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


# Function to convert audio chunk


