import os
import json
import shutil

class ModeConfigurator:
    def __init__(self, modes_file, working_directory):
        self.modes_file = modes_file
        self.working_directory = working_directory
        self.modes = self.load_modes_from_file()

    def load_modes_from_file(self, key="interaction_modes"):
        with open(self.modes_file, 'r') as file:
            return json.load(file)[key]

    def create_mode_directory(self, mode_data):
        modes_directory = os.path.dirname(self.modes_file)
        mode = mode_data['current_mode']
        mode_directory = os.path.join(modes_directory, mode)
        
        if not os.path.exists(mode_directory):
            os.makedirs(mode_directory)
            print(f"Directory for mode {mode} created.")
        else:
            print(f"Directory for mode {mode} already exists.")
        
        return mode_directory

    def set_mode_data(self, mode):
        mode_data = self.modes.get(mode)
        if not mode_data:
            print(f"Invalid mode: {mode}")
            return

        mode_path = os.path.join(self.working_directory, 'current_mode.json')
        with open(mode_path, 'w') as file:
            json.dump(mode_data, file)
        print(f"{mode} mode has been set.")

    def load_and_display_stimuli(self, mode_directory):
        stimuli_path = os.path.join(mode_directory, 'stimuli.json')
        if not os.path.exists(stimuli_path):
            print("No stimuli file found.")
            return []

        with open(stimuli_path, 'r') as file:
            stimuli = json.load(file)
        
        print("\nSpecify:\n")
        for idx, item in enumerate(stimuli, start=1):
            print(f"{idx}: {item['description']}")
        
        return stimuli

    def configure_stimuli(self, stimuli, mode_directory):
        total_stimuli = len(stimuli)
        selection = int(input(f"\nEnter a number (1-{total_stimuli}): "))
        
        if 1 <= selection <= total_stimuli:
            selected_stimuli = stimuli[selection-1]
            source_path = os.path.join(mode_directory, selected_stimuli['stimuli'])
            destination_path = os.path.join(self.working_directory, 'current_stimuli.json')
            shutil.copy(source_path, destination_path)
            print(f"'{selected_stimuli['description']}' has been set.")
        else:
            print("Invalid selection!")

    def configure_mode(self):
        try:
            print("\nMode:\n")
            mode_names = list(self.modes.keys())
            for idx, mode in enumerate(mode_names, start=1):
                description = self.modes[mode]["description"]
                print(f"{idx}: {mode} - {description}")

            total_modes = len(self.modes)
            selection = int(input(f"\nEnter the mode number (1-{total_modes}): "))

            if 1 <= selection <= total_modes:
                mode = mode_names[selection-1]
                mode_data = self.modes[mode]
                mode_directory = self.create_mode_directory(mode_data)
                self.set_mode_data(mode)

                # Load and display stimuli options
                stimuli = self.load_and_display_stimuli(mode_directory)
                self.configure_stimuli(stimuli, mode_directory)
            else:
                print("Invalid selection!")

        except KeyboardInterrupt:
            print("\nExiting...")

def main():
    modes_path = os.getcwd()+'/config/files/interaction_modes.json'
    working_directory = os.getcwd()+'/config/files/working'
    configurator = ModeConfigurator(modes_path, working_directory)
    configurator.configure_mode()

if __name__ == "__main__":
    main()
