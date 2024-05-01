import os
import json
import shutil

class ModeConfigurator:
    def __init__(self, layout_file, characters_file, working_directory):
        self.layout_file = layout_file
        self.characters_file = characters_file
        self.working_directory = working_directory
        self.layout = self.load_json_from_file(layout_file)
        self.characters = self.load_json_from_file(characters_file)

    def load_json_from_file(self, filename):
        with open(filename, 'r') as file:
            data = json.load(file)
            if "characters" in filename: 
                return data.get("characters", [])  # Safely return the list or an empty list if not found
            return data  
  
    def dump_layout(self):
        # print("Current characters data:", self.characters)
        for lay in self.layout:
            channel = lay['default_channel']
            for ters in self.characters:
                if ters['default_channel'] == channel:
                    ters['io'] = lay['io']
                    ters['addr'] = lay['addr']

        # Wrapping the list of characters in a dictionary with the 'characters' key
        data_to_write = {"characters": self.characters}

        with open(self.characters_file, 'w') as file:
            json.dump(data_to_write, file, indent=4)  # Writing the dictionary to file

        print(f"\n\033[32mConfig {self.characters_file} has been updated with the new layout.\033[0m")

def main():
    layout_file = os.getcwd()+'/config/files/working/current_layout.json'
    characters_file = os.getcwd()+'/config/files/working/current_characters.json'
    working_directory = os.getcwd()+'/config/files/working'
    configurator = ModeConfigurator(layout_file, characters_file, working_directory)
    configurator.dump_layout()

if __name__ == "__main__":
    main()
