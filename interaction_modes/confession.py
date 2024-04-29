from typing import Callable, List
from interaction_modes.interaction import PlantoidInteraction
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent

class PlantoidConfession(PlantoidInteraction):

    mode_name = 'confession'

    def __init__(
        self,
        agents: List[PlantoidDialogueAgent],
        selection_function: Callable[[int, List[PlantoidDialogueAgent]], int],
    ) -> None:
        super().__init__(agents, selection_function)

    def step(self) -> tuple[str, str]:
        # 1. choose the next speaker
        # speaker_idx = self.select_next_speaker(self._step, self.agents, self.last_speaker_idx)
        speaker = self.agents[self.last_speaker_idx]

        self.increment_speaker_idx()
        if self.last_speaker_idx == len(self.agents):
            self.reset_speaker_idx()

        # human is selected
        if speaker.is_human == True:

            print('\n\n\033[92mHuman selected ({speaker.name})\033[0m')
            # 2. next (human) speaker sends message
            speaker.speak(self.agents, speaker.name, use_streaming=False)
            message = speaker.listen_for_speech(self._step)

        else:

            # 2. next speaker sends message
            message = speaker.send()
            speaker.speak(self.agents, message)

        # 3. everyone receives message
        for receiver in self.agents:
            receiver.receive(speaker.name, message)

        # 4. increment time
        self._step += 1

        return speaker.name, message