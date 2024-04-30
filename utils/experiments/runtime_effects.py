import os
from elevenlabs.client import ElevenLabs
from elevenlabs import save

class AudioGenerator:
    def __init__(self, voice_id, api_key):
        self.voice_id = voice_id
        self.client = ElevenLabs(api_key=api_key)  # Use the passed api_key directly
        self.utterances = ["oh", "um", "hrm", "go on", "ugh", "what", "yeah"]

    def generate_and_save_audios(self):
        for utterance in self.utterances:
            audio = self.client.generate(
                text=utterance,
                model="eleven_turbo_v2",
                voice=self.voice_id,
                stream=True
            )
            filepath = os.path.join(os.getcwd(), f'media/user_audio/{self.voice_id}_{utterance}.mp3')
            save(audio, filepath)
            print(f"Audio file saved: {filepath}")

# Usage
api_key = '7392d8c1aed03a77decf691927128ba3'  # You would provide the actual API key when using this
voice_id = 'Tw2LVqLUUWkxqrCfFOpw'
audio_generator = AudioGenerator(voice_id, api_key)
audio_generator.generate_and_save_audios()
