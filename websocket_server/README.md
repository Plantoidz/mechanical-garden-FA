# WebSocket Relay Server

This directory contains the websocket server implementation for the Mechanical Garden project, as well as a relay server for deploying in distributed setups.

## Architecture

### Main WebSocket Server (`server.py`)
- Runs on the main system
- Processes instructions from the interaction manager
- Streams audio data to clients
- Ports: 8888 (orchestration), 7777 (speech), 6666 (listen)

### Relay Server (`relay_server.py`)
- Acts as an intermediary between the main server and ESPs
- Runs on a Raspberry Pi or similar device on the same network as the ESPs
- Connects to the main server as a client
- Forwards instructions and audio streams to ESPs on the local network
- Ports: 8889 (orchestration), 7778 (speech)

## Setup Instructions

### Main Server
The main server is started automatically when running the Mechanical Garden application.

### Relay Server

1. Copy the relay server files to your Raspberry Pi
2. Create a `.env` file with the following variables:
   ```
   MAIN_SERVER_HOST=<IP address of the main server>
   ```
3. Install the required dependencies:
   ```
   pip install websockets python-dotenv
   ```
4. Run the relay server:
   ```
   python relay_server.py
   ```

## ESP Configuration

ESPs should be configured to connect to the relay server instead of the main server:

```
// Connect to the relay server instead of the main server
const char* wsHost = "192.168.x.x";  // IP address of the Raspberry Pi
const int orchestratePort = 8889;    // Relay orchestration port
const int speechPort = 7778;         // Relay speech port
```

## Communication Flow

1. The main server sends instructions to the relay server
2. The relay server forwards instructions to the appropriate ESP
3. The relay server connects to the main server's speech endpoint to receive audio
4. The relay server forwards audio streams to the appropriate ESP

This architecture allows ESPs to communicate with the main server even when they're on a different network. 