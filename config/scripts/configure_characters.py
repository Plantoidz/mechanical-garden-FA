import json
import os

class CharacterConfigurator:
    def __init__(self, source_file, destination_file):
        self.source_file = source_file
        self.destination_file = destination_file
        self.characters = self.load_characters()

    def load_characters(self):
        with open(self.source_file, 'r') as file:
            return json.load(file)['characters']

    def display_menu(self):
        for i, character in enumerate(self.characters, start=1):
            print(f"{i}. {character['name']}")

    def select_character(self):
        index = int(input("Enter the number for the character: ")) - 1
        if 0 <= index < len(self.characters):
            return self.characters[index]
        else:
            print("Invalid choice!")
            return self.select_character()

    def configure_characters(self):
        num_of_characters = int(input("How many characters do you want to select? "))
        while num_of_characters <= 0 or num_of_characters > len(self.characters):
            print("Invalid number. Please enter a number between 1 and the total number of characters.")
            num_of_characters = int(input("How many characters do you want to select? "))

        selected_characters = []
        selected_characters_map = {}

        for i in range(num_of_characters):
            print(f"\nSelect character {i + 1}:")
            self.display_menu()
            choice = self.select_character()
            selected_characters.append(choice)
            selected_characters_map[choice['name']] = i  # Mapping name to the default channel

        for character in selected_characters:
            if character['name'] in selected_characters_map:
                character['default_channel'] = selected_characters_map[character['name']]

        config = {"characters": selected_characters}

        with open(self.destination_file, 'w') as file:
            json.dump(config, file, indent=4)

        print(f"\nConfig saved to {self.destination_file} with the {num_of_characters} selected characters only.")

def main():
    source_path = os.getcwd()+'/config/files/characters.json'
    destination_path = os.getcwd()+'/config/files/working/current_characters.json'
    configurator = CharacterConfigurator(source_path, destination_path)
    configurator.configure_characters()

if __name__ == "__main__":
    main()
