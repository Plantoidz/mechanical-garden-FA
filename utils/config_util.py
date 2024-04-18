import os
import json

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