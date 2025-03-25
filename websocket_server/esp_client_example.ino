#include <Arduino.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

// WiFi Credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// ESP ID - unique identifier for this ESP
const char* ESP_ID = "1";  // Change this for each ESP

// Relay Server Settings
const char* wsHost = "192.168.1.200";  // IP address of Raspberry Pi running relay server
const int orchestratePort = 8889;       // Relay server orchestration port
const int speechPort = 7778;            // Relay server speech port

// WebSocket clients
WebSocketsClient orchestrateWebSocket;
WebSocketsClient speechWebSocket;

// LED pin for status indication
const int LED_PIN = 2;  // Built-in LED on most ESP32/ESP8266 boards

// Function prototypes
void setupWiFi();
void setupWebSockets();
void onOrchestrationEvent(WStype_t type, uint8_t * payload, size_t length);
void onSpeechEvent(WStype_t type, uint8_t * payload, size_t length);

void setup() {
  // Initialize serial for debugging
  Serial.begin(115200);
  Serial.println("\nESP WebSocket Client Example");
  
  // Initialize LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Setup WiFi connection
  setupWiFi();
  
  // Setup WebSocket connections
  setupWebSockets();
}

void loop() {
  // Keep the WebSocket connections alive
  orchestrateWebSocket.loop();
  speechWebSocket.loop();
  
  // Check if WiFi is still connected, reconnect if necessary
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi connection lost. Reconnecting...");
    setupWiFi();
  }
  
  // Add any other periodic tasks here
  
  delay(10);  // Small delay to prevent watchdog timer issues
}

void setupWiFi() {
  Serial.println("Connecting to WiFi...");
  
  WiFi.begin(ssid, password);
  
  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    // Blink LED while connecting
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
  
  Serial.println("");
  Serial.print("Connected to WiFi. IP address: ");
  Serial.println(WiFi.localIP());
  
  // Turn on LED when connected
  digitalWrite(LED_PIN, HIGH);
}

void setupWebSockets() {
  // Setup orchestration WebSocket
  orchestrateWebSocket.begin(wsHost, orchestratePort, "/");
  orchestrateWebSocket.onEvent(onOrchestrationEvent);
  orchestrateWebSocket.setReconnectInterval(5000);
  
  // Setup speech WebSocket
  speechWebSocket.begin(wsHost, speechPort, "/");
  speechWebSocket.onEvent(onSpeechEvent);
  speechWebSocket.setReconnectInterval(5000);
  
  Serial.println("WebSocket connections initialized");
}

void onOrchestrationEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("Orchestration WebSocket disconnected");
      break;
    case WStype_CONNECTED:
      Serial.println("Orchestration WebSocket connected");
      // Send ESP ID as first message
      orchestrateWebSocket.sendTXT(ESP_ID);
      break;
    case WStype_TEXT:
      // Handle incoming commands
      Serial.print("Received command: ");
      Serial.println((char*)payload);
      
      // Process the command
      processCommand((char*)payload);
      break;
    case WStype_BIN:
      Serial.println("Received binary data on orchestration channel");
      break;
  }
}

void onSpeechEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("Speech WebSocket disconnected");
      break;
    case WStype_CONNECTED:
      Serial.println("Speech WebSocket connected");
      // Send ESP ID as first message
      speechWebSocket.sendTXT(ESP_ID);
      break;
    case WStype_TEXT:
      Serial.println("Received text on speech channel");
      break;
    case WStype_BIN:
      // Process binary audio data
      if (length > 0) {
        Serial.print("Received audio chunk: ");
        Serial.print(length);
        Serial.println(" bytes");
        
        // Process the audio data (e.g., play through a DAC or I2S)
        processAudio(payload, length);
      } else {
        Serial.println("End of audio stream");
      }
      break;
  }
}

void processCommand(const char* command) {
  // Parse the command and take appropriate action
  // This is just a simple example - you should adapt this to your needs
  
  if (strcmp(command, "1") == 0) {
    Serial.println("Command: Listen mode");
    // Implement listening mode
    digitalWrite(LED_PIN, HIGH);
  } 
  else if (strcmp(command, "2") == 0) {
    Serial.println("Command: Think mode");
    // Implement thinking mode
    digitalWrite(LED_PIN, LOW);
    // Blink pattern
    for (int i = 0; i < 5; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  }
  else if (strcmp(command, "3") == 0) {
    Serial.println("Command: Speak mode");
    // Implement speaking mode (audio will come through the speech channel)
    
    // Blink LED faster while speaking
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(50);
      digitalWrite(LED_PIN, LOW);
      delay(50);
    }
    digitalWrite(LED_PIN, HIGH);
  }
  else {
    Serial.print("Unknown command: ");
    Serial.println(command);
  }
}

void processAudio(uint8_t* data, size_t length) {
  // This is where you would send the audio data to your audio output hardware
  // For example, using I2S or a DAC
  
  // Example: just print the first few bytes for debugging
  Serial.print("Audio data sample: ");
  for (int i = 0; i < min(8, (int)length); i++) {
    Serial.print(data[i], HEX);
    Serial.print(" ");
  }
  Serial.println();
  
  // TODO: Implement actual audio playback logic
  // This will depend on your specific hardware setup
} 