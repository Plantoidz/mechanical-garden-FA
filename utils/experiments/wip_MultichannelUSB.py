def get_device_with_max_channels():
    devices = sd.query_devices()
    max_channels = 0
    max_device_id = None

    for device in devices:
        if device['max_output_channels'] > max_channels:
            max_channels = device['max_output_channels']
            max_device_id = device['index']
            # print(f"We have {max_channels} channels")

    if max_device_id is None:
        raise ValueError("No suitable device found.")
    
    return max_device_id, max_channels

def route_to_channel(self, channel, text, character, audio_data, filename, max_channels, max_device_id, final_text):
    character = self.get_assigned_character(channel)
    if character is None:
        print(f"No character assigned to channel {channel}.")
        return

    # Load audio file using pydub from disk
    # TODO: just read the audio data, it will save on IO
    sound = AudioSegment.from_file(filename, format="mp3")

    # Convert sound to numpy array and normalize
    samples = np.array(sound.get_array_of_samples()).astype(np.float32) / (2**15)
    # print(max_channels) #8
    # print(max_device_id) #0
    max_output_channels = sd.query_devices(max_device_id)['max_output_channels']

    if max_channels == 2:
        channel = 0

    if channel >= max_output_channels:
        raise ValueError(f"The device only has {max_channels} output channel(s).")

    # Create an empty array with the correct number of output channels
    zeros = np.zeros((len(samples), max_output_channels), dtype=np.float32)

    # Copy the mono audio data to the desired channel
    zeros[:, channel] = samples

    # Wait for previous sound to finish
    # self.audio_playback_complete.wait()

    # Lock sound playback
    with self.sound_playback_lock:
        # Reset the event indicating that sound playback has started
        self.audio_playback_complete.clear()

        # Stream the audio 
        print(f"\n\n{character.name} is speaking on {channel}:\n\n{final_text}")
        with sd.OutputStream(device=max_device_id, channels=max_output_channels, samplerate=sound.frame_rate) as stream:
            stream.write(zeros)

            # # TODO: Add a listener here to indicate Plantoid is speaking

        # # Reset the event for the next run
        self.audio_playback_complete.set()
        # playsound("global/media/cleanse.mp3", block=False)

    pass