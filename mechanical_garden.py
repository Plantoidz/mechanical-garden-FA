from context.interaction_manager import InteractionManager
from config.scripts.select_llm import get_llm
import os

def run_program():
    print("Hello Mechanical Garden!")
    
    # get the llm
    llm = get_llm()

    # instantiate the InteractionManager
    interaction_manager = InteractionManager(llm)

    # start the interaction
    interaction_manager.run_interaction()

def config_mode():
    os.system("python config/scripts/check_config.py")

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
    print("2. Check Config (WIP)")
    print("3. Config Mode")
    print("4. Config Characters")
    print("5. Config Services")
    print("6. Config Audio (WIP)")
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
