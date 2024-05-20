import pyaudio
import websocket
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define the server's port as a variable
PORT = 7777
RATE = 16000

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open a stream for audio output
stream = p.open(
    output=True,
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
)

# Create a WebSocket object
ws = websocket.WebSocket()

try:
    # Connect to the server
    ws.connect(f"ws://localhost:{PORT}")
    logging.info(f"Connected to ws://localhost:{PORT}")

    # Continuously receive data from the WebSocket and play it
    while True:
        data = ws.recv()
        # print("data received")
        stream.write(data)
except Exception as e:
    logging.error(f"An error occurred: {e}")
finally:
    # Clean up resources
    ws.close()
    stream.stop_stream()
    stream.close()
    p.terminate()
    logging.info("Resources have been cleaned up.")
