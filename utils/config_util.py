import os
import json
# import sounddevice as sd

def read_character_config():
    config_path = os.getcwd()+'/config/files/working/current_characters.json'

    with open(config_path, 'r') as file:
        character_config = json.load(file)
    
    return character_config

def read_interaction_mode_config():
    config_path = os.getcwd()+'/config/files/working/current_mode.json'

    with open(config_path, 'r') as file:
        mode_config = json.load(file)
    
    return mode_config

def read_addendum_config(interaction_mode):
    config_path = os.getcwd()+f'/config/files/working/current_stimuli.json'

    with open(config_path, 'r') as file:
        mode_config = json.load(file)
    
    return mode_config

def read_services_config():
    config_path = os.getcwd()+f'/config/files/working/current_services.json'

    with open(config_path, 'r') as file:
        mode_config = json.load(file)
    
    return mode_config

# ANSI color codes
COLORS = {"green": "\033[32m", "red": "\033[31m", "yellow": "\033[33m", "blue": "\033[34m", "green": "\033[32m", "reset": "\033[0m"
}

# def print_default_audio_devices():
#     """ Print the default audio input and output devices along with their channel counts """
#     try:
#         # Query information about the default input device
#         default_input_device_info = sd.query_devices(sd.default.device[0], 'input')
#         # Query information about the default output device
#         default_output_device_info = sd.query_devices(sd.default.device[1], 'output')
        
#         # Print the name and channel count of the input device
#         print(f"{COLORS['blue']}Audio input through{COLORS['reset']}", f"{COLORS['green']}{default_input_device_info['name']}{COLORS['reset']}", f"{COLORS['blue']}with{COLORS['reset']}", f"{COLORS['green']}{default_input_device_info['max_input_channels']}", f"channels{COLORS['reset']}")

#         # Print the name and channel count of the output device
#         print(f"\n{COLORS['blue']}Audio output through{COLORS['reset']}", f"{COLORS['green']}{default_output_device_info['name']}{COLORS['reset']}", f"{COLORS['blue']}with{COLORS['reset']}", f"{COLORS['green']}{default_output_device_info['max_output_channels']}", f"channels{COLORS['reset']}")
    
#     except Exception as e:
#         print(f"Error retrieving audio device information: {e}")

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
        os.getcwd()+"/config/files/working/current_services.json",
        os.getcwd()+"/config/files/working/current_mode.json",
        os.getcwd()+"/config/files/working/current_characters.json",
        os.getcwd()+"/config/files/working/current_stimuli.json"
    ]

    print("\nCurrent configuration:\n")

    for filepath in config_files:
        read_and_display_file(filepath)
    # print_default_audio_devices()