import pyaudio
import websocket
import threading
import time
import argparse
import subprocess

p = pyaudio.PyAudio()

stream = p.open(output=True, format=pyaudio.paInt16, channels=1, rate=16000)

ws_orchestrate = None  # WebSocket connection for orchestrate instructions
ws_stream = None       # WebSocket connection for audio stream

# Start MPV process with stdin enabled
mpv_process = subprocess.Popen(['mpv', '--no-terminal', '--idle', '--force-seekable=no', '-'],
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def on_message(ws, message):
    if message is None:
        print("Received None message, closing WebSocket connection")
        ws.close()
        return

    print("Received: ", message)
    if message == "3":
        print("Opening connection to ws://localhost:7777")
        connect_to_stream()

def on_stream_message(ws, message):
    print(len(message), type(message))
    if len(message) == 0:
        print("Received None message in stream, closing WebSocket connection")
        ws.close()
        return

    print(f"Received message of size: {len(message)} bytes")
    try:
        stream.write(message)
        # mpv_process.stdin.write(message)
        # mpv_process.stdin.flush()
    except Exception as e:
        print(f"Error writing to stream: {e}")

def on_open(ws, esp_id):
    print("Connected to WebSocket server at ws://localhost:8888")
    ws.send(esp_id)

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws):
    print("WebSocket closed")

def receive_messages(ws):
    try:
        while True:
            message = ws.recv()
            if not message:
                break
            on_message(ws, message)
    except Exception as e:
        print(f"Error receiving message: {e}")
    finally:
        ws.close()

def receive_stream(ws):
    try:
        while True:
            message = ws.recv()
            if not message:
                break
            on_stream_message(ws, message)
    except Exception as e:
        print(f"Error receiving stream: {e}")
    finally:
        ws.close()

def connect_to_orchestrate(esp_id):
    global ws_orchestrate
    retry_delay = 2  # Retry delay in seconds

    while True:
        try:
            ws_orchestrate = websocket.create_connection("ws://localhost:8888")
            on_open(ws_orchestrate, esp_id)
            receive_messages(ws_orchestrate)
        except Exception as e:
            print(f"WebSocket connection to orchestrate port failed: {e}, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

def connect_to_stream():
    global ws_stream
    retry_delay = 2  # Retry delay in seconds

    while True:
        try:
            ws_stream = websocket.create_connection("ws://localhost:7777")
            receive_stream(ws_stream)
            break
        except Exception as e:
            print(f"WebSocket connection to stream port failed: {e}, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

def main():
    parser = argparse.ArgumentParser(description="WebSocket client for streaming audio.")
    parser.add_argument('--esp_id', type=str, required=True, help="The value to send on WebSocket open.")
    args = parser.parse_args()

    try:
        threading.Thread(target=connect_to_orchestrate, args=(args.esp_id,)).start()
    except KeyboardInterrupt:
        print("Terminating connection...")
        if ws_orchestrate:
            ws_orchestrate.close()
        if ws_stream:
            ws_stream.close()
        stream.stop_stream()
        stream.close()
        p.terminate()

        # # MPV
        # mpv_process.stdin.write(b"quit\n")
        # mpv_process.stdin.flush()
        # mpv_process.stdin.close()
        # mpv_process.terminate()

if __name__ == "__main__":
    main()
