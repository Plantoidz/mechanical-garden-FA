import torch
import os
import time
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import pyaudio
import torchaudio
import numpy as np
import io
# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

# List available 🐸TTS models
print(TTS().list_models())

# # Init TTS
# tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# # Run TTS
# # ❗ Since this model is multi-lingual voice cloning model, we must set the target speaker_wav and language
# # Text to speech list of amplitude values as output
# wav = tts.tts(text="Hello world!", speaker_wav=os.getcwd()+"/utils/experiments/DA_message.wav", language="en")
# # Text to speech to a file
# tts.tts_to_file(text="Hello world!", speaker_wav=os.getcwd()+"/utils/experiments/DA_message.wav", language="en", file_path=os.getcwd()+"/output.wav")

print("Loading model...")
config = XttsConfig()
config.load_json(os.getcwd()+"/models/v2.0.2/config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir=os.getcwd()+"/models/v2.0.2/", use_deepspeed=False)
# model.cuda()

print("Computing speaker latents...")
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[os.getcwd()+"/utils/experiments/DA_message.wav"])

print("Inference...")
t0 = time.time()
chunks = model.inference_stream(
    "It took me quite a long time to develop a voice and now that I have it I am not going to be silent.",
    "en",
    gpt_cond_latent,
    speaker_embedding
)

p = pyaudio.PyAudio()

stream = p.open(output=True, format=pyaudio.paInt16, channels=1, rate=24000)

wav_chunks = []
for i, chunk in enumerate(chunks):
    if i == 0:
        print(f"Time to first chunck: {time.time() - t0}")
    print(f"Received chunk {i} of audio length {chunk.shape[-1]}")

    wav_chunks.append(chunk)
    # Convert tensor to numpy array
    # chunk_np = chunk.squeeze().unsqueeze(0).cpu()

    buff = io.BytesIO()                                                                                                                                            
    # torch.save(chunk_np, buff)     
    torchaudio.save(uri=buff, src=chunk.squeeze().unsqueeze(0).cpu(), sample_rate=24000, format="wav")      

    print(f'buffer: {len(buff.getvalue())}')      

    # print(len(chunk_np), type(chunk_np))
    
    # # Convert numpy array to bytes-like object
    # chunk_bytes = chunk_np.astype(np.int16).tobytes()

    # print(len(chunk_bytes))
    
    # # Write the bytes-like object to the audio stream
    stream.write(buff.getvalue())

stream.stop_stream()
stream.close()
p.terminate()

wav = torch.cat(wav_chunks, dim=0)
torchaudio.save("xtts_streaming.wav", wav.squeeze().unsqueeze(0).cpu(), 24000)
