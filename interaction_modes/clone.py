from typing import Callable, List
from interaction_modes.interaction import PlantoidInteraction
from plantoid_agents.clone_agent import PlantoidCloneAgent

class PlantoidClone(PlantoidInteraction):

    mode_name = 'clone'

    def __init__(
        self,
        agents: List[PlantoidCloneAgent],
        selection_function: Callable[[int, List[PlantoidCloneAgent]], int],
    ) -> None:
        super().__init__(agents, selection_function)

    def enunciate(self, intro_message: str):
        # playsound(os.getcwd()+"../media/cleanse.mp3")
        print('\n\033[94m' + 'Enunciating: ' + '\033[0m' + '\033[92m' +  f'\n{intro_message}'  + '\033[0m')

        speaker = self.agents[self.get_first_non_human_idx()]
        speaker.speak(self.agents, intro_message, use_streaming=False)

        self.set_speaker_idx(self.get_first_non_human_idx(), idx_type="last")
        self.inject(speaker.name, intro_message)

    def step(self) -> tuple[str, str]:
        # 1. choose the next speaker
        speaker_idx = self.select_next_speaker(self._step, self.agents, self.last_speaker_idx)
        self.set_speaker_idx(speaker_idx, idx_type="current")
        speaker = self.agents[speaker_idx]

        # human is selected
        if speaker.is_human == True:

            print('\nWaiting for human...\n')

            # 2. next (human) speaker sends message
            # speaker.speak(self.agents, speaker.name, use_streaming=False)
            message = speaker.listen_for_speech(self.agents, self._step)

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