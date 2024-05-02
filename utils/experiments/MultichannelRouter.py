import soundcard as sc
import shutil
import subprocess
import numpy as np
from pydub import AudioSegment
import io
from typing import Iterator, Union

def magicstream(audio_stream: Iterator[bytes], number_string: str) -> bytes:
    # Select the default speaker
    default_speaker = sc.default_speaker()
    channels_total = default_speaker.channels  # Number of channels

    # Collect all audio bytes to return
    audio = b""

    # Process each chunk of bytes in the audio stream
    for chunk in audio_stream:
        if chunk is not None:
            ### Attempt 1, works but sped up audio
            # Convert bytes to an AudioSegment
            # Assuming the audio format is MP3; change 'format="mp3"' if different
            segment = AudioSegment.from_file(io.BytesIO(chunk), format="mp3")

            # Get raw audio data as numpy array
            samples = np.array(segment.get_array_of_samples(), dtype=np.float32)

            # Normalize the samples to the range -1.0 to 1.0
            samples = samples / (2**15)

            # Create a silence signal for other channels
            zeros = np.zeros(len(samples))
    
            # Create a multi-channel signal with silence on every channel except the target one
            all_channels_signal = [zeros] * channels_total
            all_channels_signal[int(number_string)] = samples

            # Play samples through the default speaker
            default_speaker.play(np.column_stack(all_channels_signal), samplerate=segment.frame_rate)

            # Store original audio bytes
            audio += chunk

    return audio


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
