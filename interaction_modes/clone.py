from typing import Callable, List
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent

class PlantoidClone:

    mode_name = 'clone'

    def __init__(
        self,
        agents: List[PlantoidDialogueAgent],
        selection_function: Callable[[int, List[PlantoidDialogueAgent]], int],
    ) -> None:
        self.agents = agents
        self._step = 0
        self.select_next_speaker = selection_function
        self.last_speaker_idx = 0

    def increment_speaker_idx(self):
        self.last_speaker_idx += 1

    def set_speaker_idx(self, idx: int):
        self.last_speaker_idx = idx

    def reset(self):
        for agent in self.agents:
            agent.reset()

    def inject(self, name: str, message: str):
        """
        Initiates the conversation with a {message} from {name}
        """
        for agent in self.agents:
            agent.receive(name, message)

        # increment time
        self._step += 1

    def step(self) -> tuple[str, str]:
        # 1. choose the next speaker
        speaker_idx = self.select_next_speaker(self._step, self.agents, self.last_speaker_idx)
        self.set_speaker_idx(speaker_idx)
        speaker = self.agents[speaker_idx]

        # human is selected
        if speaker.name == "Human":

            print('Human Selected')

            # 2. next (human) speaker sends message
            message = speaker.listen_for_speech()

        else:

            # 2. next speaker sends message
            message = speaker.send()
            speaker.speak(message)

        # 3. everyone receives message
        for receiver in self.agents:
            receiver.receive(speaker.name, message)

        # 4. increment time
        self._step += 1

        return speaker.name, message