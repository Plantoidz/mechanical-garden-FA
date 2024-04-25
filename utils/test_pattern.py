import soundcard as sc
import numpy as np

def config_confirm():
    default_speaker = sc.default_speaker()
    print("Default Speaker:", default_speaker.name)
    print("Speaker ID:", default_speaker.id)
    print("Channels Available:", default_speaker.channels)

def tone(frequency=440, duration=0.5, samplerate=44100):
    """Generate a simple sinusoidal waveform with fade-in and fade-out."""
    t = np.arange(int(samplerate * duration)) / samplerate
    waveform = 0.5 * np.sin(2 * np.pi * frequency * t)
    # Create a fade-in and fade-out effect
    fade_length = int(samplerate * 0.1)  # Fade over 100ms
    fade_in = np.linspace(0, 1, fade_length)
    fade_out = np.linspace(1, 0, fade_length)
    # Apply fades to the waveform
    waveform[:fade_length] *= fade_in
    waveform[-fade_length:] *= fade_out
    return waveform

def play_on_channel(channel, channels_total, duration=1, samplerate=44100):
    """Play an ascending tone only on a specific channel with no popping."""
    frequency = 440 + channel * 50  # This line can be customized for different frequencies
    signal = tone(frequency, duration, samplerate)
    
    # Create a silence signal for other channels
    zeros = np.zeros(int(samplerate * duration))
    
    # Create a multi-channel signal with silence on every channel except the target one
    all_channels_signal = [zeros] * channels_total
    all_channels_signal[channel] = signal
    
    # Get the default speaker
    default_speaker = sc.default_speaker()
    default_speaker.play(np.column_stack(all_channels_signal), samplerate)

# Example usage
default_speaker = sc.default_speaker()
print("\nDefault Speaker:", default_speaker.name)
print("Speaker ID:", default_speaker.id)
print("Channels Available:", default_speaker.channels)
channels_total = default_speaker.channels  # Number of channels
print(f"\nStarting {default_speaker.channels} channel test on {default_speaker.name}")
for channel in range(channels_total):
    print(f"\nPlaying frequency {440 + channel * 50} Hz on channel {channel + 1}")
    play_on_channel(channel, channels_total, duration=2, samplerate=44100)
print(f"\nFinished {default_speaker.channels} channel test on {default_speaker.name}")