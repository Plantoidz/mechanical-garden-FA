import os
import multiprocessing
from multiprocessing import Queue, Event, current_process, Manager
import sys

import utils.config_util as config_util
# from plantoid_agents.lib.MultichannelRouter import setup_magicstream

import processes.interaction_manager_process as interaction_manager_process
import processes.websocket_server_process as websocket_server_process

from RealtimeTTS import TextToAudioStream, SystemEngine, CoquiEngine, AzureEngine, ElevenlabsEngine

import logging

def initialize_coqui_engine():
    logging.info("Initializing Coqui TTS engine...")
    return CoquiEngine(
        model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        level=logging.DEBUG,
    )

def run_program(loop: bool = True):
    print("\n\033[94mHello Mechanical Garden!\033[0m")

    ctx = multiprocessing.get_context('fork')
    
    queues = {
        "speech": ctx.Queue(),
        "listen": ctx.Queue(),
        "esp_ws": ctx.Queue(),
        "instruct": ctx.Queue(),
    }

    events = {
        "speech": ctx.Event(),
        "listen": ctx.Event(),
    }

    engines = {
        "local_tts": initialize_coqui_engine(),
    }

    # Start the WebSocket server in a separate process
    websocket_process = ctx.Process(target=websocket_server_process.run, args=(queues, events))
    websocket_process.start()

    # Start the InteractionManager in a separate process
    interaction_process = ctx.Process(target=interaction_manager_process.run, args=(queues, events, engines, loop))
    interaction_process.start()

    try:
        while interaction_process.is_alive() or loop:
            pass
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        websocket_process.terminate()
        interaction_process.terminate()
        websocket_process.join()
        interaction_process.join()

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

def main():
    if 'RUNNING_IN_DOCKER' in os.environ:
        print("Running in Docker environment")
        run_program()
    else:
        if (len(sys.argv) > 1 and sys.argv[1] == "run"):
            run_program(loop=False)
            exit()

        #while True:
        else:
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
                exit()
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    # multiprocessing.freeze_support()
    main()
