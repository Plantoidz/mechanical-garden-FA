import os
import json
from elevenlabs.client import ElevenLabs
from elevenlabs import save

api_key = os.environ.get("ELEVENLABS_API_KEY")

class AudioGenerator:
    def __init__(self, voice_id, api_key):
        self.voice_id = voice_id
        self.client = ElevenLabs(api_key=api_key)  # Use the passed api_key directly
        self.utterances = ["oh", "oh.", "oh?", "um", "hrm", "hrmmmmm", "go on", "ugh", "uh", "uh?", "eh?", "interesting!", "yeah?", "yes?", "okay", "sure thing.", "i see", "right", "really?", "really.", "oh, really?", "ah", "mhm.", "ooh", "ahh", "hmm", "huh.", "huh!", "huh??", "kay."]

    def generate_and_save_audios(self):
        for utterance in self.utterances:
            filepath = os.path.join(os.getcwd(), f'media/runtime_effects/{self.voice_id}_{utterance}.mp3')
            if not os.path.exists(filepath):  # Check if the file already exists
                audio = self.client.generate(
                    text=utterance,
                    model="eleven_turbo_v2",
                    voice=self.voice_id,
                    stream=True
                )
                save(audio, filepath)
                print(f"\033[32mAudio file saved: {filepath}\033[0m")
            else:
                print(f"\033[91mFile already exists and was not regenerated: {filepath}\033[0m")

# Path where the JSON file is located
destination_path = os.path.join(os.getcwd(), 'config', 'files', 'working', 'current_characters.json')

# Read the JSON file
with open(destination_path, 'r') as file:
    data = json.load(file)

# Extract all voice IDs
voice_ids = [character['eleven_voice_id'] for character in data.get('characters', [])]

# Initialize and use the AudioGenerator for each voice ID
for voice_id in voice_ids:
    audio_generator = AudioGenerator(voice_id, api_key)
    audio_generator.generate_and_save_audios()
