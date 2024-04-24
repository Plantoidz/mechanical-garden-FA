from DeepgramTranscription import DeepgramTranscription
from dotenv import load_dotenv
import logging

# Configuration — this is sloppy, fix later
load_dotenv()
#Deepgram
transcription = DeepgramTranscription(sample_rate=48000, device_index=3)
transcription.start_listening()
utterance = transcription.get_final_result()