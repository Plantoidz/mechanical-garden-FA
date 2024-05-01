from context.interaction_manager import InteractionManager

import os

import utils.config_util as config_util

def run_program():
    print("\nHello Mechanical Garden!")
    
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
    os.system("$(which python3) config/scripts/configure_modes.py")

def config_characters():
    os.system("$(which python3) config/scripts/configure_characters.py")

def config_services():
    os.system("$(which python3) config/scripts/configure_services.py")

def config_network():
    os.system("$(which python3) config/scripts/configure_network.py")

def add_human_participant():
    os.system("$(which python3) config/scripts/add_human_participant.py")

def dump_layout():
    os.system("$(which python3) config/scripts/dump_layout.py")

def generate_runtime_effects():
    os.system("$(which python3) config/scripts/generate_runtime_effects.py")

def config_audio():
    os.system("$(which python3) config/scripts/configure_audio.py")

def test_audio():
    os.system("$(which python3) config/scripts/test_pattern.py")

def show_menu():
    print("\nMenu:\n")
    print("1. Run Program")
    print("2. Check Config")
    print("3. Config Mode")
    print("4. Config Characters")
    print("5. Add Human Participant")
    print("6. Dump Layout")
    print("7. Generate Runtime Effects")
    print("8. Config Services")
    print("9. Config Audio Devices")
    print("10. Test Audio")
    print("11. Exit")

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
            add_human_participant()
        elif choice == '6':
            dump_layout()
        elif choice == '7':
            generate_runtime_effects()
        elif choice == '8':
            config_services()
        elif choice == '9':
            config_audio()
        elif choice == '10':
            test_audio()
        elif choice == '11':
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")
