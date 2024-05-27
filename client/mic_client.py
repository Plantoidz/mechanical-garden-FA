import pyaudio
import websocket
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the port number as a variable
PORT = 8888

# Define the WebSocketApp
ws_app = None

def record_microphone(stream, ws):
    CHUNK = 1024
    while True:
        data = stream.read(CHUNK)
        logging.info("Recording audio chunk")
        ws.send(data, websocket.ABNF.OPCODE_BINARY)
        logging.info("Sent audio data to websocket server")

def on_message(ws, message):
    logging.info(f"Received message: {message}")

def on_error(ws, error):
    logging.error(f"An error occurred: {error}")

def on_close(ws, close_status_code, close_msg):
    logging.info("WebSocket connection closed")

def on_open(ws):
    logging.info(f"Connected to WebSocket server at ws://localhost:{PORT}")
    ws.send("1")
    logging.info("Sent initial message '1' to WebSocket server")

    p = pyaudio.PyAudio()

    # Obtain the index of available mic
    mic_device_index = None
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
                    rate=32000,
                    input=True,
                    frames_per_buffer=1024,
                    input_device_index=mic_device_index)

    logging.info("Microphone stream opened")

    threading.Thread(target=record_microphone, args=(stream, ws)).start()

if __name__ == "__main__":
    websocket.enableTrace(False)
    uri = f'ws://localhost:{PORT}'
    ws_app = websocket.WebSocketApp(uri,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
    ws_app.on_open = on_open

    ws_app.run_forever()
