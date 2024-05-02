import soundcard
import shutil
import subprocess
import numpy
from pydub import AudioSegment
import io
from typing import Iterator, Union
import multiprocessing
import threading

samplerate = 44100

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()
channel_index_value = multiprocessing.Value("i", 0)
decoder_child_process = None
player_child_process = None

def restart_magicstream():
    cleanup_magicstream()
    setup_magicstream()

def cleanup_magicstream():
    global decoder_child_process
    global player_child_process
    global input_queue
    global output_queue
    while not input_queue.empty():
        input_queue.get()
    while not output_queue.empty():
        output_queue.get()
    decoder_child_process.kill()
    player_child_process.kill()

def setup_magicstream():
    global decoder_child_process
    global player_child_process
    global channel_index_value

    print("Setting up magicstream processes.")

    # Huge hack just to get the processes working
    if not decoder_child_process:
        decoder_child_process = multiprocessing.Process(target=decode_audio, args=(channel_index_value, input_queue, output_queue))
        player_child_process = multiprocessing.Process(target=play_audio, args=(channel_index_value, input_queue, output_queue))
        decoder_child_process.start()
        player_child_process.start()

def decode_audio(channel_index_value, input_queue, output_queue):
    while True:
        input_data = input_queue.get()

        segment = AudioSegment.from_file(io.BytesIO(input_data), format="mp3")
        samples = numpy.array(segment.get_array_of_samples(), dtype=numpy.float32)

        output_queue.put(samples)

def play_audio(channel_index_value, input_queue, output_queue):
    while True:
        samples = output_queue.get()
        default_speaker = soundcard.default_speaker()

        samples = samples / (2**15)
        zeros = numpy.zeros(len(samples))
        # print(f"Number of channels: {default_speaker.channels=}")
        all_channels_signal = [zeros] * default_speaker.channels
        with channel_index_value.get_lock():
            # print(f"Using channel number {channel_index_value.value}")
            all_channels_signal[channel_index_value.value] = samples

        default_speaker.play(numpy.column_stack(all_channels_signal), samplerate=samplerate)


def magicstream(audio_stream: Iterator[bytes], channel_number: str, stop_event: threading.Event) -> bytes:
    global input_queue
    setup_magicstream()

    with channel_index_value.get_lock():
        channel_index_value.value = int(channel_number)
        # print(f"Setting channel number to {channel_index_value.value}")

    # Process each chunk of bytes in the audio stream

    for chunk in audio_stream:
        if stop_event.is_set():
            print("Magicstream - stopped by stop event.")
            restart_magicstream()
            break
        if chunk is not None:
            input_queue.put(chunk)

    # Don't kill child processes here because they're expensive to spin up and can be reused
