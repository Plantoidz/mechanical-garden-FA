from websocket_server.relay_server import run_relay_server

def run():
    """Run the relay server as a process"""
    print("\n\033[94mStarting WebSocket Relay Server!\033[0m")
    run_relay_server()

if __name__ == "__main__":
    run() 