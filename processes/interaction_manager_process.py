from context.interaction_manager import InteractionManager
import os

def run(queues, events, engines, loop):
    # Instantiate the InteractionManager
    interaction_manager = InteractionManager(queues, events, engines)

    try:
        while True:
            # Start the interaction
            interaction_manager.run_interaction()
            if(not loop):
                print("KILLING PROCESSSES")
                thread.interrupt_main()
                os.kill(os.getpid())
    except KeyboardInterrupt:
        print("Exiting interaction.")

if __name__ == "__main__":
    run()