from litellm import completion
from litellm.utils import CustomStreamWrapper
from typing import Any, Generator
from elevenlabs.client import ElevenLabs, AsyncElevenLabs
from elevenlabs import stream, Voice, VoiceSettings, play
import os
from dotenv import load_dotenv

load_dotenv(override=True)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

class TextStreamer:
    def __init__(self):
        """
        Initialize the TextStreamer with a buffer for full captured text.
        """
        self.full_text = ""  # Buffer to store the full text

    def capture_and_stream_text(self, response_stream):
        """
        Capture the full text from a response stream while yielding chunks for streaming.
        """
        if isinstance(response_stream, str):
            self.full_text = response_stream
            yield response_stream
            return

        for chunk in response_stream:
            if 'choices' in chunk and chunk['choices'][0].get('delta', {}).get('content'):
                delta = chunk.choices[0].delta
                text_chunk = delta.content
                self.full_text += text_chunk  # Append to the buffer
                yield text_chunk  # Yield the current chunk
                print(text_chunk, end='', flush=True)

    def get_full_text(self):
        """
        Retrieve the full captured text.
        """
        return self.full_text

client = ElevenLabs(
  api_key=ELEVENLABS_API_KEY
)

# Instantiate the TextStreamer
text_streamer = TextStreamer()

# Stream text and capture the full response
response_stream = completion(
    model="ollama/llama3",
    messages=[{"content": "respond in 20 words. hot dogs or hamburgers?", "role": "user"}],
    stream=True
)

# Generate audio while capturing and streaming the text
audio_stream = client.generate(
    text=text_streamer.capture_and_stream_text(response_stream),  # Pass the generator method directly
    model="eleven_multilingual_v2",
    voice=Voice(
        voice_id="U1GQwcMnhqbt0tBVawvu",
        settings=VoiceSettings(
            stability=0.55,
            similarity_boost=1.0,
            style=0.25,
            use_speaker_boost=True,
        )
    ),
    stream=True,
)

# Stream the audio
stream(audio_stream)

# Retrieve and print the full captured text
final_text = text_streamer.get_full_text()
print("\nFinal Captured Text:", final_text)
