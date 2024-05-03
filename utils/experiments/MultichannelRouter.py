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
channel_index_value = multiprocessing.Value("i", 0)
decoder_child_process = None
player_child_process = None
done_event = multiprocessing.Event()

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
    global done_event

    print("Setting up magicstream processes.")

    # Huge hack just to get the processes working
    if not decoder_child_process:
        decoder_child_process = multiprocessing.Process(target=decode_audio, args=(channel_index_value, input_queue, output_queue))
        player_child_process = multiprocessing.Process(target=play_audio, args=(done_event, channel_index_value, input_queue, output_queue))

        decoder_child_process.start()
        player_child_process.start()

def decode_audio(channel_index_value, input_queue, output_queue):
    while True:
        input_data = input_queue.get()

        segment = AudioSegment.from_file(io.BytesIO(input_data), format="mp3")
        samples = numpy.array(segment.get_array_of_samples(), dtype=numpy.float32)

        output_queue.put(samples)

def play_audio(done_event, channel_index_value, input_queue, output_queue):
    while True:
        samples = output_queue.get()
        default_speaker = soundcard.default_speaker()
        number_of_channels = default_speaker.channels

        samples = samples / (2**15)
        zeros = numpy.zeros(len(samples))
        # print(f"Number of channels: {default_speaker.channels=}")
        all_channels_signal = [zeros] * number_of_channels
        with channel_index_value.get_lock():
            index = channel_index_value.value

            # If using an audio device that has less channels than the character's
            # channel index, we hardcode the value
            if channel_index_value.value >= number_of_channels:
                index = 1

            # print(f"Using channel number {channel_index_value.value}")
            all_channels_signal[index] = samples

        default_speaker.play(numpy.column_stack(all_channels_signal), samplerate=samplerate)

        if output_queue.empty():
            done_event.set()

def magicstream(audio_stream: Iterator[bytes], channel_number: str) -> bytes:
    global input_queue
    setup_magicstream()

    done_event.clear()
    
    with channel_index_value.get_lock():
        channel_index_value.value = int(channel_number)
        # print(f"Setting channel number to {channel_index_value.value}")

    # Process each chunk of bytes in the audio stream
    for chunk in audio_stream:
        if chunk is not None:
            input_queue.put(chunk)

    done_event.wait()
