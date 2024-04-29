from typing import Callable, List
from interaction_modes.interaction import PlantoidInteraction
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent

class PlantoidConversation(PlantoidInteraction):

    mode_name = 'conversation'

    def __init__(
        self,
        agents: List[PlantoidDialogueAgent],
        selection_function: Callable[[int, List[PlantoidDialogueAgent]], int],
    ) -> None:
        super().__init__(agents, selection_function)

  