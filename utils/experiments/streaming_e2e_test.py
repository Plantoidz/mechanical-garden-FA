from elevenlabs import play, stream, save
from elevenlabs.client import ElevenLabs
from litellm import completion, acompletion
from DeepgramTranscription import DeepgramTranscription
import traceback
import asyncio
from simpleaichat import AIChat, AsyncAIChat
import os
from dotenv import load_dotenv
import logging

# Configuration — this is sloppy, fix later
load_dotenv()
tts = ElevenLabs(api_key="")
llm_config = "ollama_chat/llama3"
personality = open("personality.txt").read().strip()
ai = AIChat(system=personality, api_key="", model="gpt-4-turbo")

#Deepgram
transcription = DeepgramTranscription()
transcription.start_listening()
utterance = transcription.get_final_result()
        
#Whisper
# mic = WhisperMic()
# playsound('media/beep_start.wav')
# utterance = mic.listen()
# print(f"I heard: {utterance}")

async def audio_streaming():
    audio_stream = tts.generate(
        text=text_streaming(utterance),
        voice="5g2h5kYnQtKFFdPm8PpK",
        model="eleven_turbo_v2",
        stream=True
    )
    stream(audio_stream)
    
def text_streaming(utterance):
    response = completion(
        model=llm_config, 
        messages=[{"content": utterance, "role": "user"}], 
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta
            text_chunk = delta.content
            yield text_chunk
            print(text_chunk, end='', flush=True)

async def main():
    counter = 0
    while True:
        await asyncio.sleep(0)
        await audio_streaming()
        counter += 1
        print(f"\nInteraction count: {counter}\n")

if __name__ == "__main__":
    asyncio.run(main())

# def main():
#     counter = 0
#     while True:
#         # mic = WhisperMic()
#         transcription = DeepgramTranscription()
#         playsound('media/beep_start.wav')
#         # utterance = mic.listen()
#         transcription.start_listening()
#         utterance = transcription.get_final_result()
#         print(f"I heard: {utterance}")
#         response = ai(utterance)
#         print(f"I said: {response}")
#         counter += 1
#         print(f"Interaction count: {counter}")
#         audio_stream = client.generate(
#             text=f"{response}",
#             # text=text_stream(),
#             model="eleven_turbo_v2",
#             voice="5g2h5kYnQtKFFdPm8PpK",
#             stream=True
#         )
#         stream(audio_stream)
