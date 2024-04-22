import sys
from pathlib import Path
from typing import Any, Dict, List, Type

from interaction_modes.conversation import PlantoidConversation
from interaction_modes.kiosk import PlantoidKiosk
from interaction_modes.debate import PlantoidDebate
from interaction_modes.clone import PlantoidClone

from plantoid_agents.dialogue_agent import PlantoidDialogueAgent
from plantoid_agents.debate_agent import PlantoidDebateAgent
from plantoid_agents.clone_agent import PlantoidCloneAgent

from utils.config_util import read_character_config, read_interaction_mode_config, read_addendum_config
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
        
        if selection_function == 'kiosk':
            return speaker_selection.select_next_speaker_with_human_kiosk
        
        if selection_function == 'debate':
            return speaker_selection.select_next_speaker_with_human_debate
        
        if selection_function == 'clone':
            return speaker_selection.select_next_speaker_with_human_clone
        
    def get_bidding_function(self, selection_function: str) -> any:
        """
        Retrieves the selection function based on the provided string.
        """
        if selection_function == 'conversation':
            return speaker_selection.generate_character_bidding_template_conversation
        
        if selection_function == 'kiosk':
            return speaker_selection.generate_character_bidding_template_kiosk
        
        if selection_function == 'debate':
            return speaker_selection.generate_character_bidding_template_debate
        
        if selection_function == 'clone':
            return speaker_selection.generate_blank_bidding_template
        
    def get_plantoid_agent(self, agent_type: str) -> Type:
        """
        Retrieves the Plantoid agent based on the provided agent type.
        """
        if agent_type == 'conversation':
            return PlantoidDialogueAgent
        
        if agent_type == 'kiosk':
            return PlantoidDebateAgent
        
        if agent_type == 'debate':
            return PlantoidDebateAgent
        
        if agent_type == 'clone':
            return PlantoidCloneAgent
        
    def get_interaction_mode(self, interaction_mode: str) -> Type:
        """
        Retrieves the interaction mode based on the provided interaction mode.
        """
        if interaction_mode == 'conversation':
            return PlantoidConversation
        
        if interaction_mode == 'kiosk':
            return PlantoidKiosk
        
        if interaction_mode == 'debate':
            return PlantoidDebate
        
        if interaction_mode == 'clone':
            return PlantoidClone
        
    def get_interaction_addendum(self, interaction_mode: str) -> List[str]:
        """
        Retrieves the interaction addendum based on the provided interaction mode.
        """
        if interaction_mode == 'conversation':
            return []
        
        if interaction_mode == 'kiosk':
            kiosk_config = read_addendum_config(interaction_mode)
            return [kiosk_config['reasoning_prompt1']]
        
        if interaction_mode == 'debate':
            return []
        
        if interaction_mode == 'clone':
            return []
        
    def get_interaction_description(self, interaction_mode: str):
        """
        Retrieves the interaction mode based on the provided interaction mode.
        """
        if interaction_mode == 'conversation':
            return "This is a friendly conversation on exploring each other's personalities. What do you like to do for fun?"
        
        if interaction_mode == 'kiosk':
            kiosk_config = read_addendum_config(interaction_mode)
            return kiosk_config['description']
        
        if interaction_mode == 'debate':
            return "This is a heated debate on the topic of ETH vs BTC cryptocurrency. Let your hearts loose!"
        
        if interaction_mode == 'clone':
            return "You are a clone of me!"
        
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
        interaction_description = self.get_interaction_description(use_interaction_mode)
        interaction_addendum = self.get_interaction_addendum(use_interaction_mode)
        plantoid_agent = self.get_plantoid_agent(use_agent_type)
        selection_function = self.get_selection_function(use_selection_function)
        bidding_function = self.get_bidding_function(use_bidding_template)

        return {
            "interaction_mode": interaction_mode,
            "interaction_description": interaction_description,
            "interaction_addendum": interaction_addendum,
            "plantoid_agent": plantoid_agent,
            "characters": use_characters,
            "bidding_function": bidding_function,
            "selection_function": selection_function,
        }
    
    def get_system_message(
        self,
        character: any,
        interaction_mode_name: str,
        interaction_description: str,
        interaction_addendum: List[str],
        use_message_type: str = 'raw',
        word_limit: int = 25, # TODO: move to config
    ):
        
        character_name = character['name']
        character_system_message_input = character['system_message']
        character_description = character['description']

        if use_message_type == 'raw':

            character_system_message = character_setup.get_raw_system_message(character_system_message_input)
        
        if use_message_type == 'specified':

            character_header = character_setup.generate_character_header(
                interaction_mode_name,
                interaction_description,
                interaction_addendum,
                # specified_topic,
                character_name,
                character_description,
                word_limit,
            )

            character_system_message = character_setup.generate_character_system_message(
                # specified_topic,
                word_limit,
                character_name,
                character_header,
            )
        
        return character_system_message


    def generate_character_context(
        self,
        characters: Dict[str, List[Dict[str, Any]]],
        plantoid_agent: Type,
        bidding_function: any,
        interaction_mode_name: str,
        interaction_description: str,
        interaction_addendum: List[str],
    ) -> List[Any]:
        """
        Generates context for each character based on the configurations.
        """
        character_objects = []

        # print(characters)

        for character in characters:
            character_name = character['name']
            character_description = character['description']
            character_voice_id = character['eleven_voice_id']

            system_message = self.get_system_message(
                character,
                interaction_mode_name,
                interaction_description,
                interaction_addendum,
                use_message_type='specified'
            )

            bidding_template = bidding_function(character_description)

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
        interaction_description = interaction_context['interaction_description']
        interaction_addendum = interaction_context['interaction_addendum']
        plantoid_agent = interaction_context['plantoid_agent']
        characters = interaction_context['characters']
        bidding_function = interaction_context['bidding_function']
        selection_function = interaction_context['selection_function']

        character_context = self.generate_character_context(
            characters,
            plantoid_agent,
            bidding_function,
            interaction_mode.mode_name,
            interaction_description,
            interaction_addendum,
        )

        self.start_interaction(
            interaction_mode,
            character_context,
            selection_function,
        )
