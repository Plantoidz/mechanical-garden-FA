from context.interaction_manager import InteractionManager
from config.scripts.select_llm import get_llm


if __name__ == "__main__":

    print("Hello Mechanical Garden!")
    
    # get the llm
    llm = get_llm()

    # instantiate the InteractionManager
    interaction_manager = InteractionManager(llm)

    # start the interaction
    interaction_manager.run_interaction()


