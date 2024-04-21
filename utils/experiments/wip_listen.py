import json
import os
from datetime import datetime

class PlantoidAgent:
    def __init__(self, role, channel, personality, address, agent_id=None):
        self.role = role
        self.channel = channel
        self.personality = personality
        self.address = address
        self.id = agent_id if agent_id is not None else str(int(datetime.now().timestamp()))
        self.message_file = f"working/{self.id}_messages.json"
        self.ensure_file()

    def ensure_file(self):
        if not os.path.exists(self.message_file):
            with open(self.message_file, 'w') as file:
                json.dump([], file)

    async def listen(self, speakafter=False):
        # Simulated transcription start and retrieval
        transcription = DeepgramTranscription()
        transcription.start_listening()
        prompt = transcription.get_final_result()

        # Append user's message to the conversation
        self.append_message(prompt, "user")

        if speakafter:
            # Simulate generating and speaking a response
            response = self.generate_response(prompt)
            self.append_message(response, "assistant")
            await self.audio_streaming(response)

    def append_message(self, content, role):
        with open(self.message_file, 'r+') as file:
            messages = json.load(file)
            messages.append({"content": content, "role": role})
            file.seek(0)
            json.dump(messages, file)

    def generate_response(self, prompt):
        # Placeholder for generating a response based on the prompt
        return "This is a response based on your input."

    async def audio_streaming(self, content):
        # Placeholder for streaming audio
        print(f"Speaking: {content}")

class DeepgramTranscription:
    def start_listening(self):
        print("Listening...")

    def get_final_result(self):
        return "Simulated transcript of user's speech"

# Example usage:
agent1 = PlantoidAgent(role="1", channel="1", personality="1", address="1")
