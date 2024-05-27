from websocket_server.server import run_websocket_server

def run(queues):

    print("\n\033[94mHello WebSocket Server!\033[0m")
    run_websocket_server(queues)

if __name__ == "__main__":
    run()
