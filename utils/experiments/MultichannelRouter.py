import soundcard as sc
import shutil
import subprocess
from typing import Iterator, Union

# # Print the name and details of the default speaker
# def config_confirm 
#     default_speaker = sc.default_speaker()
#     print("Default Speaker:", default_speaker.name)
#     print("Speaker ID:", default_speaker.id)
#     print("Channels Available:", default_speaker.channels)

# def is_installed(lib_name: str) -> bool:
#     lib = shutil.which(lib_name)
#     if lib is None:
#         return False
#     return True

def magicstream(audio_stream: Iterator[bytes], number_string: str) -> bytes:
    channel_map = {
        "0": "FL",
        "1": "FR",
        "2": "FC",
        "3": "BL",
        "4": "BR",
        "5": "BC",
        "6": "SL",
        "7": "SR"
    }

    # Get the channel mapping ID based on the input number string
    channel_map_id = channel_map.get(str(number_string))
    if channel_map_id is None:
        raise ValueError("Invalid number string. Must be a number from 0 to 7.")

    # Build the audio filter string
    channel_routing_flag = f"--af=lavfi=[pan=octagonal|{channel_map_id}=c0]"
    mpv_command = [
        "mpv", "--no-cache", "--no-terminal", 
        channel_routing_flag,
        "--audio-channels=octagonal" , 
        "--", "fd://0"
    ]
    mpv_process = subprocess.Popen(
        mpv_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    audio = b""

    for chunk in audio_stream:
        if chunk is not None:
            mpv_process.stdin.write(chunk)  # type: ignore
            mpv_process.stdin.flush()  # type: ignore
            audio += chunk
    if mpv_process.stdin:
        mpv_process.stdin.close()
    mpv_process.wait()


    return audio

import subprocess

def magicplay(mp3_filepath: str, number_string: str) -> bytes:
    channel_map = {
        "0": "FL",
        "1": "FR",
        "2": "FC",
        "3": "BL",
        "4": "BR",
        "5": "BC",
        "6": "SL",
        "7": "SR"
    }

    # Get the channel mapping ID based on the input number string
    channel_map_id = channel_map.get(str(number_string))
    if channel_map_id is None:
        raise ValueError("Invalid number string. Must be a number from 0 to 7.")

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
