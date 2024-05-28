import asyncio
import websockets
import logging
import subprocess
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)

# Start MPV process with stdin enabled
mpv_process = subprocess.Popen(['mpv', '--no-terminal', '--idle', '--force-seekable=no', '-'],
                               stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Define the port number and trigger messages as variables
PORT = 7777
PLAYBACK_START_TRIGGER_MESSAGE = "START_PLAYBACK"
PLAYBACK_COMPLETE_MESSAGE = "PLAYBACK_COMPLETE"

async def receive_and_play_audio(websocket, start_event):
    await websocket.send("1")
    logging.info("Sent initial message '1' to WebSocket server")

    # Wait for playback start trigger from server
    while True:
        message = await websocket.recv()
        if message == PLAYBACK_START_TRIGGER_MESSAGE:
            logging.info("Received playback start trigger message from server")
            start_event.set()
            break

    # Receive and play audio chunks
    try:
        async for message in websocket:
            logging.info(f"Received message of size: {len(message)} bytes")

            # Assuming the received message is the base64-encoded audio chunk
            audio_chunk = message  # base64.b64decode(message)
            logging.info(f"Decoded audio chunk of size: {len(audio_chunk)} bytes")

            try:
                mpv_process.stdin.write(audio_chunk)
                mpv_process.stdin.flush()

            except Exception as e:
                logging.error(f"Error while decoding or playing audio: {e}")

        mpv_process.stdin.close()
        mpv_process.terminate()

        websocket.send(PLAYBACK_COMPLETE_MESSAGE)

    except websockets.ConnectionClosed as e:
        logging.info(f"WebSocket connection closed with code {e.code}: {e.reason}")

def monitor_mpv_and_notify(loop, websocket, start_event):
    try:
        start_event.wait()  # Wait for the start event to be set
        mpv_process.wait()  # Wait for the mpv process to complete
        logging.info("Playback complete, sending termination message.")

        # Terminate the mpv process
        mpv_process.terminate()
        mpv_process.wait()

        # Send termination message to server
        asyncio.run_coroutine_threadsafe(websocket.send(PLAYBACK_COMPLETE_MESSAGE), loop)
        logging.info("Sent playback termination message to WebSocket server")
        
        # Close the websocket connection
        asyncio.run_coroutine_threadsafe(websocket.close(), loop)
    except Exception as e:
        logging.error(f"Error while monitoring MPV process: {e}")

async def main():
    uri = f"ws://localhost:{PORT}"
    async with websockets.connect(uri) as websocket:
        start_event = threading.Event()

        # Start a thread to monitor mpv and send the termination message
        loop = asyncio.get_event_loop()
        monitor_thread = threading.Thread(target=monitor_mpv_and_notify, args=(loop, websocket, start_event))
        monitor_thread.start()

        # Handle receiving and playing audio in the main thread
        await receive_and_play_audio(websocket, start_event)

        # Wait for the monitor thread to finish
        monitor_thread.join()

if __name__ == "__main__":
    asyncio.run(main())
