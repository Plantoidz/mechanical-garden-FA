import soundcard
import shutil
import subprocess
import numpy
from pydub import AudioSegment
import io
from typing import Iterator, Union
import multiprocessing
import time
import threading

samplerate = 44100

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()
channel_index_value = multiprocessing.Value("i", 0)
decoder_child_process = None
player_child_process = None
stream_input_event = multiprocessing.Event()
done_event = multiprocessing.Event()
start_event = multiprocessing.Event()

SAMPLE_PLAY_COLLECTION_LIMIT = 1
SAMPLE_LOOP_NOOP_ITERATIONS = 2
SAMPLE_LOOP_SLEEP_TIME = 0.25
START_TIMER_DURATION = 1

mpv_processes = []

def setup_magicstream():
    global decoder_child_process
    global player_child_process
    global channel_index_value
    global stream_input_event
    global done_event
    global start_event
    global input_queue
    global output_queue

    # Huge hack just to get the processes working
    if not decoder_child_process:
        print("-------SETTING UP MAGICSTREAM BACKGROUND PROCESSES-------")

        input_queue = multiprocessing.Queue()
        output_queue = multiprocessing.Queue()

        decoder_child_process = multiprocessing.Process(target=decode_audio, args=(channel_index_value, input_queue, output_queue))
        player_child_process = multiprocessing.Process(target=play_audio, args=(start_event, stream_input_event, done_event, channel_index_value, input_queue, output_queue))

        decoder_child_process.start()
        player_child_process.start()

def restart_magicstream():
    global decoder_child_process
    global player_child_process
    global channel_index_value
    global stream_input_event
    global done_event
    global start_event
    global input_queue
    global output_queue

    print("-------TRYING TO RESET MAGICSTREAM BACKGROUND PROCESSES AND QUEUES-------")

    # small hack just to not bother if these processes aren't already started because using another config
    if decoder_child_process:

        print("-------RESETTING MAGICSTREAM BACKGROUND PROCESSES AND QUEUES-------")

        print("-------MAGICSTREAM EMPTYING QUEUES-------")
        while not input_queue.empty():
            input_queue.get()
        while not output_queue.empty():
            output_queue.get()

        print("-------MAGICSTREAM CLOSING QUEUES-------")
        input_queue.close()
        output_queue.close()

        print("-------MAGICSTREAM QUEUES DESTROYED-------")

        decoder_child_process.kill()
        player_child_process.kill()
        done_event.set()
        stream_input_event.clear()
        decoder_child_process = None
        player_child_process = None

        print("-------MAGICSTREAM CLEANED UP-------")

        # setup_magicstream()

def start_timer(start_event):
    time.sleep(START_TIMER_DURATION)
    start_event.set()

def decode_audio(channel_index_value, input_queue, output_queue):
    # print("Starting magicstream audio decoder process")
    while True:
        audio_to_decode = []
        while not input_queue.empty():
            audio_to_decode.append(input_queue.get())

        if len(audio_to_decode) == 0:
            time.sleep(0.1)
            continue

        print(f"Decoding {len(audio_to_decode)} audio segments")
        for input_data in audio_to_decode:
            try:
                input_data = input_queue.get()

                segment = AudioSegment.from_file(io.BytesIO(input_data), format="mp3")
                samples = numpy.array(segment.get_array_of_samples(), dtype=numpy.float32)

                print("Finished decoding audio segment")
                output_queue.put(samples)
            except Exception as e:
                print(f"Audio decoder exception occurred: \n{e}")

def play_audio(start_event, stream_input_event, done_event, channel_index_value, input_queue, output_queue):
    collected_samples = []
    iterations_without_playing = SAMPLE_LOOP_NOOP_ITERATIONS
    
    while True:
        if not start_event.is_set():
            time.sleep(SAMPLE_LOOP_SLEEP_TIME)
            continue

        if output_queue.empty():
            if len(collected_samples) == 0:
                # If there's nothing to do, just sleep a bit to give back time
                time.sleep(SAMPLE_LOOP_SLEEP_TIME)
                continue
        else:
            # If there are samples to collect, collect all of them
            while not output_queue.empty():
                collected_samples.append(output_queue.get())

        print(f"Collected {len(collected_samples)} samples.")

        # If there aren't enough samples yet, just decrement the counter
        if len(collected_samples) < SAMPLE_PLAY_COLLECTION_LIMIT:
            iterations_without_playing -= 1
            # print(f"Only have {len(collected_samples)} samples. Looping {iterations_without_playing} more times.")

        # If there are enough samples, or the counter is at 0, flush
        if len(collected_samples) >= SAMPLE_PLAY_COLLECTION_LIMIT or iterations_without_playing == 0:
            print(f"Going to play {len(collected_samples)} samples...")
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

                    # print(f"Speaking on channel {channel_index_value.value}")
                    all_channels_signal[index] = samples

                # print("Playing chunk.")
                default_speaker.play(numpy.column_stack(all_channels_signal), samplerate=samplerate)

            # reset counter and sample collector
            iterations_without_playing = SAMPLE_LOOP_NOOP_ITERATIONS
            collected_samples.clear()
            print("Samples played. Reset and clear.")

            if output_queue.empty() and not stream_input_event.is_set() and input_queue.empty():
                # print("All magicstream output done. Setting done event.")
                done_event.set()

def magicstream(audio_stream: Iterator[bytes], channel_number: str, stop_event: threading.Event = None) -> bytes:
    global channel_index_value
    global stream_input_event
    global done_event
    global start_event
    global input_queue

    setup_magicstream()

    print("-------MAGICSTREAM STARTING-------")

    # print("starting magicstream playback")
    done_event.clear()
    stream_input_event.set()

    print("-------MAGICSTREAM WAITING FOR BUFFER-------")
    start_event.clear()
    timer_process = multiprocessing.Process(target=start_timer, args=(start_event,))
    timer_process.start()
    
    with channel_index_value.get_lock():
        channel_index_value.value = int(channel_number)

    print("-------MAGICSTREAM STARTING TO SEND CHUNKS TO DECODER-------")

    # Process each chunk of bytes in the audio stream
    for chunk in audio_stream:
        if stop_event and stop_event.is_set():
            print("-------MAGICSTREAM BAILING EARLY BECAUSE OF STOP EVENT-------")
            return
        if chunk is not None:
            input_queue.put(chunk)

    print("-------MAGICSTREAM DONE SENDING CHUNKS TO DECODER-------")

    # Allow playback process to finish (not really)
    stream_input_event.clear()

    print("-------MAGICSTREAM WAITING FOR DONE-------")

    # Wait until the audio play process is done playing audio
    done_event.wait()

    print("-------MAGICSTREAM COMPLETE-------")
