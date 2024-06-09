from RealtimeTTS import TextToAudioStream, SystemEngine, CoquiEngine, AzureEngine, ElevenlabsEngine
from litellm import completion
import time
import multiprocessing

def litellm(msg):
    response = completion(
        model="ollama/llama3", 
        messages=msg, 
        api_base="http://localhost:11434",
        stream=True
    )
    return response

def litestream(msg):
    r = litellm(msg)
    for chunk in r:
        if (text_chunk := chunk["choices"][0]["delta"].get("content")) is not None:
            yield text_chunk

def my_text_start_func():
    print("text stream started")

def my_text_stop_func():
    print("text stream stopped")

def my_audio_start_func():
    print("audio stream started")

def my_audio_stop_func():
    print("audio stream stopped")

def on_audio_chunk(chunk):
    print("playing of len", len(chunk))

def main():
    print("loading engine..")
    engine = CoquiEngine(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2"
        # model_name="tts_models/en/ek1/tacotron2"
    )
    print("setting up the engine")
    stream = TextToAudioStream(
        engine=engine,
        on_text_stream_start=my_text_start_func,
        on_text_stream_stop=my_text_stop_func,
        on_audio_stream_start=my_audio_start_func,
        on_audio_stream_stop=my_audio_stop_func,
    )
    print("feeding the words")
    
    messages = [{"content": "Write a three-sentence relaxing speech", "role": "user"}]
    r = litestream(messages)
    print("received ----->  ", r)
    stream.feed(r)
    
    print("playing")
    stream.play_async(on_audio_chunk=on_audio_chunk)

    while stream.is_playing():
        time.sleep(0.1)
    print("done...")

if __name__ == '__main__':
    multiprocessing.freeze_support()  # Optional
    main()
