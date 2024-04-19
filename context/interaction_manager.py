import sys
from pathlib import Path
from typing import Any, Dict, List, Type

from interaction_modes.conversation import PlantoidConversation
from interaction_modes.debate import PlantoidDebate

from plantoid_agents.dialogue_agent import PlantoidDialogueAgent
from plantoid_agents.debate_agent import PlantoidDebateAgent

from utils.config_util import read_character_config, read_interaction_mode_config
import context.character_setup as character_setup # TODO: roll this into context config
import context.speaker_selection as speaker_selection # TODO: roll this into context config


class InteractionManager:
    def __init__(self, llm: Any):
        self.llm = llm  # Language Learning Model or any contextually relevant model

    def get_selection_function(self, selection_function: str) -> any:
        """
        Retrieves the selection function based on the provided string.
        """
        if selection_function == 'conversation':
            return speaker_selection.select_next_speaker_with_human_conversation
        
        if selection_function == 'debate':
            return speaker_selection.select_next_speaker_with_human_debate
        
    def get_bidding_function(self, selection_function: str) -> any:
        """
        Retrieves the selection function based on the provided string.
        """
        if selection_function == 'conversation':
            return speaker_selection.generate_character_bidding_template_conversation
        
        if selection_function == 'debate':
            return speaker_selection.generate_character_bidding_template_debate
        
    def get_plantoid_agent(self, agent_type: str) -> Type:
        """
        Retrieves the Plantoid agent based on the provided agent type.
        """
        if agent_type == 'conversation':
            return PlantoidDialogueAgent
        
        if agent_type == 'debate':
            return PlantoidDebateAgent
        
    def get_interaction_mode(self, interaction_mode: str) -> Type:
        """
        Retrieves the interaction mode based on the provided interaction mode.
        """
        if interaction_mode == 'conversation':
            return PlantoidConversation
        
        if interaction_mode == 'debate':
            return PlantoidDebate

    def get_interaction_context(self) -> Dict[str, Any]:
        """
        Retrieves and configures the interaction context based on predefined configurations.
        """
        mode_config = read_interaction_mode_config()
        character_config = read_character_config()

        use_interaction_mode = mode_config['current_mode']
        use_agent_type = mode_config['agent_type']
        use_bidding_template = mode_config['bidding_template']
        use_selection_function = mode_config['selection_function']
        use_characters = character_config['characters']

        print(f"Using interaction mode: {use_interaction_mode}")
        print(f"Using agent type: {use_agent_type}")
        print(f"Using bidding template: {use_bidding_template}")
        print(f"Using selection function: {use_selection_function}")
        print("Using characters:", [x["name"] for x in use_characters])

        interaction_mode = self.get_interaction_mode(use_interaction_mode)
        plantoid_agent = self.get_plantoid_agent(use_agent_type)
        selection_function = self.get_selection_function(use_selection_function)
        bidding_function = self.get_bidding_function(use_bidding_template)

        return {
            "interaction_mode": interaction_mode,
            "plantoid_agent": plantoid_agent,
            "characters": use_characters,
            "bidding_function": bidding_function,
            "selection_function": selection_function,
        }

    def generate_character_context(
        self,
        characters: Dict[str, List[Dict[str, Any]]],
        plantoid_agent: Type,
        bidding_function: any,
    ) -> List[Any]:
        """
        Generates context for each character based on the configurations.
        """
        character_objects = []

        # print(characters)

        for character in characters:
            character_name = character['name']
            character_system_message = character['system_message']
            character_voice_id = character['eleven_voice_id']

            # TODO: move to character setup
            bidding_template = bidding_function(character_system_message)
            system_message = character_setup.get_raw_system_message(character_system_message) # TODO: generalize

            character_object = plantoid_agent(
                name=character_name,
                system_message=system_message, 
                model=self.llm,
                bidding_template=bidding_template,
                eleven_voice_id=character_voice_id
            )

            character_objects.append(character_object)

        return character_objects

    def start_interaction(
        self,
        interaction_mode: Type,
        characters: List[Any],
        selection_function: any,
        max_iters: int = 10
    ) -> None:
        """
        Starts the interaction simulation using the provided interaction mode and characters.
        """
        simulator = interaction_mode(
            agents=characters,
            selection_function=selection_function
        )
        simulator.reset()

        n = 0

        print('Running interaction mode...')
        while n < max_iters:
            name, message = simulator.step()
            # print(f"({name}): {message}")
            n += 1

    def run_interaction(self) -> None:
        """
        Main method to setup and run the interaction based on the retrieved context.
        """
        interaction_context = self.get_interaction_context()

        # get the context
        interaction_mode = interaction_context['interaction_mode']
        plantoid_agent = interaction_context['plantoid_agent']
        characters = interaction_context['characters']
        bidding_function = interaction_context['bidding_function']
        selection_function = interaction_context['selection_function']

        character_context = self.generate_character_context(characters, plantoid_agent, bidding_function)
        self.start_interaction(interaction_mode, character_context, selection_function)
