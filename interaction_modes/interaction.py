from typing import Callable, List, Union, Any
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent
from plantoid_agents.debate_agent import PlantoidDebateAgent
from plantoid_agents.clone_agent import PlantoidCloneAgent
from elevenlabs import play, stream, save
from elevenlabs.client import ElevenLabs
import os
import keyboard
from playsound import playsound
from plantoid_agents.events.speak import Speak

class Interruption:
    def update(self, forced_speaker_idx):
        pass  # Implement this method in subclasses

class PlantoidInteraction:

    mode_name = 'interaction'

    def __init__(
        self,
        agents: List[Union[PlantoidDialogueAgent, PlantoidDebateAgent, PlantoidCloneAgent]],
        selection_function: Callable[[int, List[Union[PlantoidDialogueAgent, PlantoidDebateAgent, PlantoidCloneAgent]]], int],
    ) -> None:
        self.agents = agents
        self._step = 0
        self.select_next_speaker = selection_function
        self.last_speaker_idx = 0
        self.current_speaker_idx = 0
        self.listeners = []

    def register_listener(self, listener: Interruption):
        self.listeners.append(listener)

    def notify_listeners(self, forced_speaker_idx):
        for listener in self.listeners:
            listener.update(forced_speaker_idx)

    def increment_speaker_idx(self, idx_type: str = "current"):

        if idx_type == "current":
            self.current_speaker_idx += 1

        if idx_type == "last":
            self.last_speaker_idx += 1

    def set_speaker_idx(self, idx: int, idx_type: str = "current"):

        if idx_type == "current":
            self.current_speaker_idx = idx

        if idx_type == "last":
            self.last_speaker_idx = idx

    def reset_speaker_idx(self, idx_type: str = "current"):

        if idx_type == "current":
            self.current_speaker_idx = 0
        
        if idx_type == "last":
            self.last_speaker_idx = 0

    def get_first_non_human_idx(self):
        for idx, agent in enumerate(self.agents):
            if agent.is_human == False:
                return idx

    def reset(self):
        print("\nNew stimulus. Resetting conversation...\n")
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

    #todo: need to restore speaking in enunciation, and it's reated to the first turn behavior
    # ENUNCIATE SIMULUS HERE
    def enunciate(self, intro_message: str):

        # playsound(os.getcwd()+"/media/cleanse.mp3", block=False)
        print('\n\033[94m' + 'Enunciating: ' + '\033[0m' + '\033[92m' +  f'\n{intro_message}'  + '\033[0m')
        speaker = self.agents[self.get_first_non_human_idx()]
        # print('speaker name === ', speaker.name)
        # print("INTRO MSG = ", intro_message)
        speaker.speak(self.agents, intro_message, use_streaming=False)

        self.set_speaker_idx(self.get_first_non_human_idx(), idx_type="last")
        self.inject(speaker.name, intro_message)

    def wait_for_enter(self):
        print("Press Enter to notify listeners...")
        keyboard.wait('enter')
        self.notify_listeners(self.current_speaker_idx)

    def step(self) -> tuple[str, str]:
        # 1. choose the next speaker
        if forced_speaker_idx is not None:
            speaker_idx = forced_speaker_idx
        else:
            speaker_idx = self.select_next_speaker(self._step, self.agents, self.last_speaker_idx)
        self.set_speaker_idx(speaker_idx, idx_type="current")
        speaker = self.agents[speaker_idx]

        # print(f"Current speaker index: {self.current_speaker_idx}")
        # print(f"Last speaker index: {self.last_speaker_idx}")

        # human is selected
        if speaker.is_human == True:

            print('\n\n\033[92mHuman selected (' + speaker.name + ')\033[0m')

            # ENUNCIATE SPEAKER NAME HERE
            last_speaker = self.agents[self.last_speaker_idx]
            last_speaker.speak(self.agents, speaker.name, use_streaming=False)

            message = speaker.listen_for_speech(self.agents, self._step)
        else:

            # 2. next speaker sends message
            message = speaker.send()
            speaker.speak(self.agents, message)

        # 3. everyone receives message
        for receiver in self.agents:
            receiver.receive(speaker.name, message)

        # 4. increment time
        self.set_speaker_idx(speaker_idx, idx_type="last")
        self._step += 1

        return speaker.name, message
    
    def log_conversation(self, log_file_path: str, speaker: PlantoidDialogueAgent, message: str):
        print(f"{speaker.name} says: {message}")
        with open(log_file_path, "a") as f:
            f.write(f"{speaker.name} says: {message}\n")

    def log_agents(self, log_file_path: str):
        with open(log_file_path, "w") as f:
            for agent in self.agents:
                f.write(f"{agent.name}\n")
                f.write(f"{agent.__class__.__name__}\n")
                f.write(f"{agent.name}")
                f.write(f"{agent.is_human}")
                f.write(f"{agent.system_message}")
                f.write(f"{agent.bidding_template}")
                f.write(f"{agent.prefix}")
                f.write(f"{agent.eleven_voice_id}")
                f.write(f"{agent.channel_id}")
                f.write(f"{agent.tunnel}")
                f.write(f"{agent.socket}")
                f.write(f"{agent.callback}")
                f.write(f"{agent.addr}")
                f.write(f"{agent.use_model_type}")
                f.write(f"{agent.use_streaming}")
                f.write(f"{agent.__dict__}\n")
                f.write("\n")