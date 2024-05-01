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
            return json.load(file)
           

  
    def dump_layout(self):
        print(self.characters)  # Add this to check the structure
        for lay in self.layout:
            channel = lay['default_channel']
            for ters in self.characters:
                if(ters['default_channel'] == channel):
                    ters['io'] = lay['io']
                    ters['addr'] = lay['addr']

        with open(self.characters_file, 'w') as file:
            json.dump(self.characters, file, indent=4)

        print(f"\nConfig {self.characters_file} has been updated with the new layout.")


def main():
    layout_file = os.getcwd()+'/config/files/working/current_layout.json'
    characters_file = os.getcwd()+'/config/files/working/current_characters.json'
    working_directory = os.getcwd()+'/config/files/working'
    configurator = ModeConfigurator(layout_file, characters_file, working_directory)
    configurator.dump_layout()

if __name__ == "__main__":
    main()
