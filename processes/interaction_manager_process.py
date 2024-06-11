from context.interaction_manager import InteractionManager

def run(queues, events, engines):
    # Instantiate the InteractionManager
    interaction_manager = InteractionManager(queues, events, engines)

    try:
        while True:
            # Start the interaction
            interaction_manager.run_interaction()
    except KeyboardInterrupt:
        print("Exiting interaction.")

if __name__ == "__main__":
    run()