from context.interaction_manager import InteractionManager
import json
import os
import sounddevice as sd
from config.scripts.select_llm import get_llm

def run_program():
    print("Hello Mechanical Garden!")
    
    # get the llm
    llm = get_llm()

    # instantiate the InteractionManager
    interaction_manager = InteractionManager(llm)

    # start the interaction
    interaction_manager.run_interaction()

# ANSI color codes
COLORS = {"green": "\033[32m", "red": "\033[31m", "yellow": "\033[33m", "blue": "\033[34m", "green": "\033[32m", "reset": "\033[0m"
}

def print_default_audio_devices():
    """ Print the default audio input and output devices along with their channel counts """
    try:
        # Query information about the default input device
        default_input_device_info = sd.query_devices(sd.default.device[0], 'input')
        # Query information about the default output device
        default_output_device_info = sd.query_devices(sd.default.device[1], 'output')
        
        # Print the name and channel count of the input device
        print(f"{COLORS['blue']}Audio input through{COLORS['reset']}", f"{COLORS['green']}{default_input_device_info['name']}{COLORS['reset']}", f"{COLORS['blue']}with{COLORS['reset']}", f"{COLORS['green']}{default_input_device_info['max_input_channels']}", f"channels{COLORS['reset']}")

        # Print the name and channel count of the output device
        print(f"\n{COLORS['blue']}Audio output through{COLORS['reset']}", f"{COLORS['green']}{default_output_device_info['name']}{COLORS['reset']}", f"{COLORS['blue']}with{COLORS['reset']}", f"{COLORS['green']}{default_output_device_info['max_output_channels']}", f"channels{COLORS['reset']}")
    
    except Exception as e:
        print(f"Error retrieving audio device information: {e}")

def format_value(value, indent=0, color_index=0):
    """ Recursively format JSON values for printing with colors. """
    color_keys = list(COLORS.keys())[:-1]  # exclude the reset key
    current_color = COLORS[color_keys[color_index % len(color_keys)]]
    reset_color = COLORS["reset"]
    indent_space = ' ' * indent  # Compute the current level's indentation

    if isinstance(value, dict):
        formatted_items = []
        for key, val in value.items():
            # Append only a single space after the colon, and no additional indent for the value itself
            formatted_key_value = f"{indent_space}{current_color}{key}:{reset_color} {format_value(val, indent, color_index + 1)}"
            formatted_items.append(formatted_key_value)
        return "\n".join(formatted_items)
    elif isinstance(value, list):
        formatted_items = []
        # Increase indent for list elements
        for item in value:
            formatted_item = f"{indent_space}  {format_value(item, indent + 2, color_index + 1)}"
            formatted_items.append(formatted_item)
        return "\n".join(formatted_items)
    else:
        return f"{indent_space}{current_color}{value}{reset_color}"

# You can keep the read_and_display_file function unchanged
def read_and_display_file(filepath):
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            for key, value in data.items():
                formatted_value = format_value(value)
                print(f"{COLORS['blue']}{key}:{COLORS['reset']}\n{formatted_value}\n")
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
    except json.JSONDecodeError:
        print(f"Error: {filepath} could not be decoded.")


def check_config():
    config_files = [
        "config/files/working/current_services.json",
        "config/files/working/current_mode.json",
        # "config/files/working/current_addendum.json",
        "config/files/working/current_characters.json"
    ]
    print("\nCurrent configuration:\n")
    for filepath in config_files:
        read_and_display_file(filepath)
    print_default_audio_devices()

def config_mode():
    os.system("python config/scripts/configure_modes.py")

def config_characters():
    os.system("python config/scripts/configure_characters.py")

def config_services():
    os.system("python config/scripts/configure_services.py")

def config_audio():
    os.system("python config/scripts/configure_audio.py")

def test_audio():
    os.system("python config/scripts/test_pattern.py")

def show_menu():
    print("\nMenu:\n")
    print("1. Run Program")
    print("2. Check Config")
    print("3. Config Mode")
    print("4. Config Characters")
    print("5. Config Services")
    print("6. Config Audio (Linux only)")
    print("7. Test Audio")
    print("8. Exit")

if __name__ == "__main__":
    while True:
        show_menu()
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            run_program()
        elif choice == '2':
            check_config()
        elif choice == '3':
            config_mode()
        elif choice == '4':
            config_characters()
        elif choice == '5':
            config_services()
        elif choice == '6':
            config_audio()
        elif choice == '7':
            test_audio()
        elif choice == '8':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")
