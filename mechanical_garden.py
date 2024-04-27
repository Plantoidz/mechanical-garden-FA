from context.interaction_manager import InteractionManager

import os

import utils.config_util as config_util

def run_program():
    print("Hello Mechanical Garden!")
    
    # instantiate the InteractionManager
    interaction_manager = InteractionManager()

    try:

        while True:

            # start the interaction
            interaction_manager.run_interaction()

    except KeyboardInterrupt:
        print("Exiting interaction.")
        pass

def config_mode():
    os.system("$(which python) config/scripts/configure_modes.py")

def config_characters():
    os.system("$(which python) config/scripts/configure_characters.py")

def config_services():
    os.system("$(which python) config/scripts/configure_services.py")

def config_network():
    os.system("$(which python) config/scripts/configure_network.py")

def add_human_participant():
    os.system("python3 config/scripts/add_human_participant.py")

def config_audio():
    os.system("$(which python) config/scripts/configure_audio.py")

def test_audio():
    os.system("$(which python) config/scripts/test_pattern.py")

def show_menu():
    print("\nMenu:\n")
    print("1. Run Program")
    print("2. Check Config")
    print("3. Config Mode")
    print("4. Config Characters")
    print("5. Config Services")
    print("6. Add Human Participant")
    print("7. Config Audio (Linux only)")
    print("8. Test Audio")
    print("9. Exit")

if __name__ == "__main__":
    while True:
        show_menu()
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            run_program()
        elif choice == '2':
            config_util.check_config()
        elif choice == '3':
            config_mode()
        elif choice == '4':
            config_characters()
        elif choice == '5':
            config_services()
        elif choice == '6':
            add_human_participant()
        elif choice == '7':
            config_audio()
        elif choice == '8':
            test_audio()
        elif choice == '9':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")
