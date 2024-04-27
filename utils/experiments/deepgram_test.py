from DeepgramTranscription_linux import DeepgramTranscription
from dotenv import load_dotenv
import logging

# Configuration — this is sloppy, fix later
load_dotenv()
#Deepgram
transcription = DeepgramTranscription(sample_rate=48000, device_index=None)
transcription.start_listening()
utterance = transcription.get_final_result()
print("Utterance is: ", utterance)