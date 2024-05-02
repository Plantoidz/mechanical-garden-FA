import soundcard
import shutil
import subprocess
import numpy
from pydub import AudioSegment
import io
from typing import Iterator, Union
import multiprocessing

samplerate = 44100

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()
decoder_child_process = None
player_child_process = None

def setup_magicstream():
    global decoder_child
    global player_child
    global decoder_child_process
    global player_child_process

    print("Setting up magicstream processes.")

    # Huge hack just to get the processes working
    if not decoder_child_process:
        decoder_child_process = multiprocessing.Process(target=decode_audio, args=(input_queue, output_queue))
        player_child_process = multiprocessing.Process(target=play_audio, args=(input_queue, output_queue))

        decoder_child_process.start()
        player_child_process.start()

def decode_audio(input_queue, output_queue):
    while True:
        input_data = input_queue.get()

        segment = AudioSegment.from_file(io.BytesIO(input_data), format="mp3")
        samples = numpy.array(segment.get_array_of_samples(), dtype=numpy.float32)

        output_queue.put(samples)

def play_audio(input_queue, output_queue):
    while True:
        samples = output_queue.get()

        samples = samples / (2**15)
        zeros = numpy.zeros(len(samples))
        all_channels_signal = [zeros] * 2
        all_channels_signal[1] = samples

        soundcard.default_speaker().play(numpy.column_stack(all_channels_signal), samplerate=samplerate)


def magicstream(audio_stream: Iterator[bytes], number_string: str) -> bytes:
    global input_queue
    setup_magicstream()

    # Process each chunk of bytes in the audio stream
    for chunk in audio_stream:
        if chunk is not None:
            input_queue.put(chunk)

def magicplay(mp3_filepath: str, number_string: str) -> bytes:
    channel_map = {
        "0": "FL",
        "1": "FR",
        "2": "FC",
        "3": "BL",
        "4": "BR",
        "5": "BC",
        "6": "WL",
        "7": "WR"
    }

    # Get the channel mapping ID based on the input number string
    channel_map_id = channel_map.get(str(number_string))
    if channel_map_id is None:
        raise ValueError("Channel map id error.")

    # Build the audio filter string
    channel_routing_flag = f"--af=lavfi=[pan=octagonal|{channel_map_id}=c0]"
    mpv_command = [
        "mpv", "--no-cache", "--no-terminal",
        channel_routing_flag,
        "--audio-channels=octagonal",
        mp3_filepath  # Directly using the MP3 file path
    ]
    
    # Execute the MPV process
    mpv_process = subprocess.Popen(
        mpv_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    # Read the processed audio data
    audio_data = b""
    while True:
        chunk = mpv_process.stdout.read(1024)  # Read data chunk by chunk
        if not chunk:
            break
        audio_data += chunk

    # Ensure the MPV process is properly cleaned up
    mpv_process.wait()

    return audio_data
