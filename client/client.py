import pyaudio
import websocket

p = pyaudio.PyAudio()

stream = p.open(output=True, format = pyaudio.paInt16, channels=1, rate = 16000)

ws = websocket.WebSocket()

ws.connect("ws://localhost:7777")

ws.send("1")

while True:
	data = ws.recv()
	stream.write(data)

ws.close()
