import asyncio
import websockets
import logging
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Relay server ports - ESPs will connect to these ports on the Raspberry Pi
RELAY_ORCHESTRATE_PORT = 8889
RELAY_SPEECH_PORT = 7778

# Main server details - this is where the relay will connect as a client
MAIN_SERVER_HOST = os.environ.get("MAIN_SERVER_HOST", "192.168.1.100")  # Default or from env
MAIN_ORCHESTRATE_PORT = 8888
MAIN_SPEECH_PORT = 7777

# Storage for connected ESP clients
esp_clients = {}  # {esp_id: {'orchestrate_ws': ws, 'speech_ws': ws}}

# Locks for thread safety when modifying the client dictionary
esp_clients_lock = asyncio.Lock()

async def register_esp(esp_id, websocket, connection_type):
    """Register an ESP connection"""
    async with esp_clients_lock:
        if esp_id not in esp_clients:
            esp_clients[esp_id] = {}
        esp_clients[esp_id][connection_type] = websocket
        logging.info(f"Registered ESP {esp_id} for {connection_type} connection")

async def unregister_esp(esp_id, connection_type):
    """Unregister an ESP connection"""
    async with esp_clients_lock:
        if esp_id in esp_clients and connection_type in esp_clients[esp_id]:
            del esp_clients[esp_id][connection_type]
            if not esp_clients[esp_id]:  # If no more connections, remove the ESP entirely
                del esp_clients[esp_id]
            logging.info(f"Unregistered ESP {esp_id} from {connection_type} connection")

async def connect_to_main_orchestrator():
    """Connects to the main server's orchestrator endpoint"""
    uri = f"ws://{MAIN_SERVER_HOST}:{MAIN_ORCHESTRATE_PORT}"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logging.info(f"Connected to main orchestrator at {uri}")
                
                # Identify as relay server to the main server
                await websocket.send("relay_server")
                
                # Process messages from main server
                async for message in websocket:
                    logging.info(f"Received orchestration message: {message}")
                    
                    # Parse the message if it's in the format "esp_id:instruction"
                    if ':' in message:
                        esp_id, instruction = message.split(':', 1)
                        
                        # Forward the instruction to the appropriate ESP
                        async with esp_clients_lock:
                            if esp_id in esp_clients and 'orchestrate_ws' in esp_clients[esp_id]:
                                try:
                                    await esp_clients[esp_id]['orchestrate_ws'].send(instruction)
                                    logging.info(f"Forwarded instruction to ESP {esp_id}: {instruction}")
                                except Exception as e:
                                    logging.error(f"Error forwarding to ESP {esp_id}: {e}")
                            else:
                                logging.warning(f"No ESP {esp_id} connected for orchestration message")
                    else:
                        # If it's a broadcast message, send to all ESPs
                        async with esp_clients_lock:
                            for esp_id, connections in esp_clients.items():
                                if 'orchestrate_ws' in connections:
                                    try:
                                        await connections['orchestrate_ws'].send(message)
                                        logging.info(f"Broadcast message to ESP {esp_id}: {message}")
                                    except Exception as e:
                                        logging.error(f"Error broadcasting to ESP {esp_id}: {e}")
        
        except Exception as e:
            logging.error(f"Connection to main orchestrator failed: {e}")
            await asyncio.sleep(5)  # Wait before reconnecting

async def relay_speech_stream(main_speech_ws, esp_id):
    """Relay speech stream from the main server to the ESP"""
    async with esp_clients_lock:
        if esp_id in esp_clients and 'speech_ws' in esp_clients[esp_id]:
            esp_speech_ws = esp_clients[esp_id]['speech_ws']
            try:
                # Relay audio chunks from main server to ESP
                async for chunk in main_speech_ws:
                    if not chunk:  # Empty chunk signals end of stream
                        await esp_speech_ws.send(b'')
                        break
                    await esp_speech_ws.send(chunk)
            except Exception as e:
                logging.error(f"Error in speech relay for ESP {esp_id}: {e}")
        else:
            logging.warning(f"No speech connection for ESP {esp_id}")

async def handle_esp_orchestration(websocket, path):
    """Handle orchestration connections from ESPs"""
    try:
        # First message should be the ESP ID
        esp_id = await websocket.recv()
        
        # Register this ESP
        await register_esp(esp_id, websocket, 'orchestrate_ws')
        
        # Set up a handler for client disconnect
        disconnect = asyncio.ensure_future(websocket.wait_closed())
        disconnect.add_done_callback(
            lambda _: asyncio.create_task(unregister_esp(esp_id, 'orchestrate_ws'))
        )
        
        # Handle messages from the ESP (if any)
        async for message in websocket:
            logging.info(f"Received message from ESP {esp_id}: {message}")
            # Here you could implement logic to forward ESP messages to the main server
            # For now, just log them
    except Exception as e:
        logging.error(f"Error in ESP orchestration handler: {e}")

async def handle_esp_speech(websocket, path):
    """Handle speech connections from ESPs"""
    try:
        # First message should be the ESP ID
        esp_id = await websocket.recv()
        
        # Register this ESP for speech
        await register_esp(esp_id, websocket, 'speech_ws')
        
        # Set up a handler for client disconnect
        disconnect = asyncio.ensure_future(websocket.wait_closed())
        disconnect.add_done_callback(
            lambda _: asyncio.create_task(unregister_esp(esp_id, 'speech_ws'))
        )
        
        # Connect to the main server's speech endpoint to receive audio
        uri = f"ws://{MAIN_SERVER_HOST}:{MAIN_SPEECH_PORT}"
        try:
            async with websockets.connect(uri) as main_speech_ws:
                logging.info(f"Connected to main speech server for ESP {esp_id}")
                await relay_speech_stream(main_speech_ws, esp_id)
        except Exception as e:
            logging.error(f"Failed to connect to main speech server: {e}")
            
    except Exception as e:
        logging.error(f"Error in ESP speech handler: {e}")

async def start_relay_server():
    """Start the relay server"""
    # Start the orchestration server for ESPs
    orchestrate_server = await websockets.serve(
        handle_esp_orchestration, 
        '', 
        RELAY_ORCHESTRATE_PORT,
        ping_interval=None
    )
    
    # Start the speech server for ESPs
    speech_server = await websockets.serve(
        handle_esp_speech,
        '',
        RELAY_SPEECH_PORT,
        ping_interval=None
    )
    
    # Connect to the main orchestrator
    asyncio.create_task(connect_to_main_orchestrator())
    
    logging.info(f"Relay server running on ports {RELAY_ORCHESTRATE_PORT}, {RELAY_SPEECH_PORT}")
    
    return orchestrate_server, speech_server

def run_relay_server():
    """Main entry point for the relay server"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    servers = loop.run_until_complete(start_relay_server())
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Relay server stopped by keyboard interrupt")
    finally:
        # Clean shutdown
        for server in servers:
            server.close()
        loop.run_until_complete(asyncio.gather(*[server.wait_closed() for server in servers]))
        loop.close()

if __name__ == '__main__':
    run_relay_server() 