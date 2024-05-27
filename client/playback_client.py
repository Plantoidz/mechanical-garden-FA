import websocket
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger().setLevel(logging.INFO)

# Start MPV process with stdin enabled
mpv_process = subprocess.Popen(['mpv', '--no-terminal', '--idle', '--force-seekable=no', '-'],
                               stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Define the port number as a variable
PORT = 7777

# WebSocket client to receive and play audio chunks
def on_message(ws, message):
    logging.info(f"Received message of size: {len(message)} bytes")

    # Assuming the received message is the base64-encoded audio chunk
    audio_chunk = message # base64.b64decode(message)
    logging.info(f"Decoded audio chunk of size: {len(audio_chunk)} bytes")

    try:
        mpv_process.stdin.write(audio_chunk)
        mpv_process.stdin.flush()
        
    except Exception as e:
        logging.error(f"Error while decoding or playing audio: {e}")

def on_error(ws, error):
    logging.error(f"An error occurred: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.info("WebSocket connection closed")

def on_open(ws):
    logging.info(f"Connected to WebSocket server at ws://localhost:{PORT}")
    ws.send("1")  # Send initial message to server
    logging.info("Sent initial message '1' to WebSocket server")

if __name__ == "__main__":
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(f"ws://localhost:{PORT}",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
