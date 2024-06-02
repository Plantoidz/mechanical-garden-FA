import asyncio
import websockets
import logging
import subprocess
import threading
import time
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)

# Define the port number and trigger messages as variables
PORT = 7777
PLAYBACK_START_TRIGGER_MESSAGE = "START_PLAYBACK"
PLAYBACK_COMPLETE_MESSAGE = "PLAYBACK_COMPLETE"
STREAM_END_MESSAGE = "END_STREAM"

# Estimated bit rate in bytes per second (e.g., 128 kbps = 16 KBps)
ESTIMATED_BIT_RATE = int(16 * 1024)
CORRECTION_FACTOR = 0.85

async def receive_and_play_audio(websocket, start_event, end_event, esp_id):
    while True:
        await websocket.send(str(esp_id))
        logging.info(f"Sent initial message '{esp_id}' to WebSocket server")

        # Wait for playback start trigger from server
        while True:
            message = await websocket.recv()
            logging.info(f"Received message from server: {message}")

            if message == STREAM_END_MESSAGE:
                logging.info("Received end of stream message from server")
                end_event.set()
                break

            start_msg = message.split(":")[0]
            agent_esp_id = int(message.split(":")[1])
            if start_msg == PLAYBACK_START_TRIGGER_MESSAGE and agent_esp_id == esp_id:
                logging.info(f"Received playback start trigger message from server for ESP ID: {esp_id}")
                start_event.set()
                break

        # Start MPV process with stdin enabled
        mpv_process = subprocess.Popen(['mpv', '--no-terminal', '--idle', '--force-seekable=no', '-'],
                                       stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        total_size = 0  # Initialize total size of received chunks
        last_chunk_time = None  # Time when the last chunk was received

        # Receive and play audio chunks
        try:
            async for message in websocket:
                if message == STREAM_END_MESSAGE:
                    logging.info("Received end of stream message from server")
                    break

                chunk_size = len(message)
                total_size += chunk_size
                last_chunk_time = time.time()

                logging.info(f"Received message of size: {chunk_size} bytes for esp id {esp_id}")

                try:
                    mpv_process.stdin.write(message)
                    mpv_process.stdin.flush()
                    logging.info("Playing audio chunk...")

                except Exception as e:
                    logging.error(f"Error while playing audio: {e}")

            # Calculate estimated playback duration
            estimated_duration = (total_size / ESTIMATED_BIT_RATE) * CORRECTION_FACTOR
            logging.info(f"Estimated playback duration: {estimated_duration:.2f} seconds")

            # Wait for the estimated duration after the last chunk
            if last_chunk_time:
                time_to_wait = last_chunk_time + estimated_duration - time.time()
                if time_to_wait > 0:
                    logging.info(f"Waiting for {time_to_wait:.2f} seconds to ensure playback completes")
                    time.sleep(time_to_wait)

            logging.info("SET END EVENT")
            end_event.set()

            # Send the quit command to mpv to ensure it terminates
            try:
                mpv_process.stdin.write(b"quit\n")
                mpv_process.stdin.flush()
                mpv_process.stdin.close()
                mpv_process.terminate()

            except Exception as e:
                logging.error(f"Error while sending quit command to MPV: {e}")

            mpv_process.wait()  # Wait for the mpv process to complete
            logging.info("MPV process completed playback")

            # Send termination message to server
            await websocket.send(PLAYBACK_COMPLETE_MESSAGE)
            logging.info("Sent playback termination message to WebSocket server")

        except websockets.ConnectionClosed as e:
            logging.info(f"WebSocket connection closed with code {e.code}: {e.reason}")
            break

async def main(esp_id):
    uri = f"ws://localhost:{PORT}"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                start_event = threading.Event()
                end_event = threading.Event()

                # Handle receiving and playing audio in the main thread
                await receive_and_play_audio(websocket, start_event, end_event, esp_id)

        except websockets.ConnectionClosed as e:
            logging.error(f"WebSocket connection closed, reconnecting in 2 seconds... {e}")
            await asyncio.sleep(2)
        except Exception as e:
            logging.error(f"Unexpected error: {e}, reconnecting in 2 seconds...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebSocket audio player with MPV.")
    parser.add_argument("--esp_id", type=int, default=None, help="ESP ID to send to the WebSocket server")
    args = parser.parse_args()

    asyncio.run(main(args.esp_id))
