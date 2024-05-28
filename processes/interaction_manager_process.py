from context.interaction_manager import InteractionManager

def run(queues, events):
    # Instantiate the InteractionManager
    interaction_manager = InteractionManager(queues, events)

    try:
        while True:
            # Start the interaction
            interaction_manager.run_interaction()
    except KeyboardInterrupt:
        print("Exiting interaction.")

if __name__ == "__main__":
    run()