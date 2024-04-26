import subprocess

def list_audio_devices():
    # Get a list of output and input devices
    result = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True)
    print("Output devices:")
    print(result.stdout)
    
    result = subprocess.run(["pactl", "list", "short", "sources"], capture_output=True, text=True)
    print("Input devices:")
    print(result.stdout)

def choose_device(device_type):
    # User chooses the device index or name
    return input(f"Enter the preferred {device_type} device name or index: ")

def set_default_device(device_name, device_type):
    # Set the chosen device as the default
    if device_type == "input":
        subprocess.run(["pactl", "set-default-source", device_name])
    else:
        subprocess.run(["pactl", "set-default-sink", device_name])

def main():
    list_audio_devices()
    output_device = choose_device("output")
    input_device = choose_device("input")
    
    set_default_device(output_device, "output")
    set_default_device(input_device, "input")

    print("Default audio devices have been set.")

if __name__ == "__main__":
    main()
