from typing import Callable, List, Union
from interaction_modes.interaction import PlantoidInteraction
from plantoid_agents.debate_agent import PlantoidDebateAgent

class PlantoidDebate(PlantoidInteraction):

    mode_name = 'debate'

    def __init__(
        self,
        agents: List[PlantoidDebateAgent],
        selection_function: Callable[[int, List[Union[PlantoidDebateAgent, PlantoidDebateAgent]]], int],
    ) -> None:
        super().__init__(agents, selection_function)
