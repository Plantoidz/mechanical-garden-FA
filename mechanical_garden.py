from interaction_modes.conversation import PlantoidConversation
from interaction_modes.debate import PlantoidDebate

from plantoid_agents.dialogue_agent import PlantoidDialogueAgent
from plantoid_agents.debate_agent import PlantoidDebateAgent

from events.listen import Listen
from events.speak import Speak
from events.think import Think

from utils.util import load_config
from config.scripts.select_llm import select_llm

if __name__ == "__main__":

    # NOTE: Not working.
    
    config = load_config()

    # instantiate the LLM to use
    use_interface = config['general']['use_llm']
    llm = select_llm(interface=use_interface)

    interaction_mode = config['general']['interaction_mode']
    interaction_agents = config['general']['interaction_agents']
    interaction_characters = None

    print("Hello Mechanical Garden!")