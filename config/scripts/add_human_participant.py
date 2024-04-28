import json

def create_character():
    name = input("\nEnter human name: ")
    description = input("Enter human description: ")

    new_character = {
        "name": name,
        "system_message": "",
        "description": description,
        "default_channel": 999,
        "eleven_voice_id": "5g2h5kYnQtKFFdPm8PpK",
        "is_human": True
    }

    return new_character

def append_to_json(character):
    try:
        with open('config/files/working/current_characters.json', 'r+') as file:
            data = json.load(file)
            characters = data.get("characters", [])
            characters.append(character)
            data["characters"] = characters
            file.seek(0)
            json.dump(data, file, indent=4)
            print("Character added successfully!")
    except FileNotFoundError:
        print("current_characters.json file not found.")

def main():
    character = create_character()
    append_to_json(character)

if __name__ == "__main__":
    main()
