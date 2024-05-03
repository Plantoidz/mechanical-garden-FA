import soundcard
import shutil
import subprocess
import numpy
from pydub import AudioSegment
import io
from typing import Iterator, Union
import multiprocessing
import time

samplerate = 44100

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()
channel_index_value = multiprocessing.Value("i", 0)
decoder_child_process = None
player_child_process = None
stream_input_event = multiprocessing.Event()
done_event = multiprocessing.Event()

def setup_magicstream():
    global decoder_child
    global player_child
    global decoder_child_process
    global player_child_process
    global channel_index_value
    global stream_input_event
    global done_event

    # print("Setting up magicstream processes.")

    # Huge hack just to get the processes working
    if not decoder_child_process:
        decoder_child_process = multiprocessing.Process(target=decode_audio, args=(channel_index_value, input_queue, output_queue))
        player_child_process = multiprocessing.Process(target=play_audio, args=(stream_input_event, done_event, channel_index_value, input_queue, output_queue))

        decoder_child_process.start()
        player_child_process.start()

def decode_audio(channel_index_value, input_queue, output_queue):
    while True:
        input_data = input_queue.get()

        try:
            segment = AudioSegment.from_file(io.BytesIO(input_data), format="mp3")
            samples = numpy.array(segment.get_array_of_samples(), dtype=numpy.float32)

            output_queue.put(samples)
        except:
            print("EXCEPTION")

def play_audio(stream_input_event, done_event, channel_index_value, input_queue, output_queue):
    collected_samples = []
    iterations_without_playing = 50
    
    while True:
        if output_queue.empty():
            # If there's nothing to do, just sleep a bit to give back time
            time.sleep(1)
            continue
        else:
            # If there are samples to collect, collec them
            collected_samples.append(output_queue.get())

        # If there aren't enough samples yet, just decrement the counter
        if len(collected_samples) < 5:
            iterations_without_playing -= 1

        # If there are enough samples, or the counter is at 0, flush
        if len(collected_samples) >= 5 or iterations_without_playing == 0:
            for samples in collected_samples:
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

                print("\nplay chunk start\n")
                default_speaker.play(numpy.column_stack(all_channels_signal), samplerate=samplerate)
                print("\nplay chunk stop\n")

            # reset counter and sample collector
            iterations_without_playing = 50
            collected_samples.clear()

            # TODO: add another event to signify input incase decoding is really slow...
            if output_queue.empty() and not stream_input_event.is_set():
                done_event.set()

def magicstream(audio_stream: Iterator[bytes], channel_number: str) -> bytes:
    global input_queue
    setup_magicstream()

    done_event.clear()
    stream_input_event.set()
    
    with channel_index_value.get_lock():
        channel_index_value.value = int(channel_number)
        # print(f"Setting channel number to {channel_index_value.value}")

    # Process each chunk of bytes in the audio stream
    for chunk in audio_stream:
        if chunk is not None:
            input_queue.put(chunk)

    # Tell the audio play process that it can flush and finish
    stream_input_event.clear()

    # Wait until the audio play process is done playing audio
    done_event.wait()
