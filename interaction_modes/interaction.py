from typing import Callable, List, Union, Any
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent
from plantoid_agents.debate_agent import PlantoidDebateAgent
from plantoid_agents.clone_agent import PlantoidCloneAgent
from elevenlabs import play, stream, save
from elevenlabs.client import ElevenLabs
import os
from datetime import datetime
from playsound import playsound
from plantoid_agents.events.speak import Speak


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
        self.humanness = 0.5
        self.agent_interrupted = False
        self.interaction_timestamp = datetime.now()

    def set_agent_interrupted(self, agent_interrupted: bool = True):
        self.agent_interrupted = agent_interrupted
        
    def interruption_callback(self, agent_interrupted, speaker_name, message):
        self.set_agent_interrupted(agent_interrupted)
        self.inject(speaker_name, message)

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
        speaker.speak(self.agents, intro_message, use_streaming=True)

        self.set_speaker_idx(self.get_first_non_human_idx(), idx_type="last")
        self.inject(speaker.name, intro_message)

    def step(self) -> tuple[str, str]:

        print("Doing interaction step: ", self._step)
        print("Agent was interrupted: ", self.agent_interrupted)

        # 1. choose the next speaker
        speaker_idx = self.select_next_speaker(
            self._step,
            self.agents,
            self.last_speaker_idx,
            self.humanness, # arg is humanness % (between 0 and 1)
            self.agent_interrupted,
        ) 

        self.set_speaker_idx(speaker_idx, idx_type="current")
        self.set_agent_interrupted(agent_interrupted=False)
        speaker = self.agents[speaker_idx]

        # print(f"Current speaker index: {self.current_speaker_idx}")
        # print(f"Last speaker index: {self.last_speaker_idx}")

        # 2. think or listen based on if human or agent
        # human is selected
        if speaker.is_human == True:

            print('\n\n\033[92mHuman selected (' + speaker.name + ')\033[0m')

            # # # ENUNCIATE SPEAKER NAME HERE
            # last_speaker = self.agents[self.last_speaker_idx]
            # last_speaker.speak(self.agents, speaker.name, use_streaming=False)
            # playsound(os.getcwd() + "/media/cleanse.mp3", block=False)

            message = speaker.listen_for_speech(self.agents, self._step, self.agents[self.get_first_non_human_idx()])
            # message = "Test human message"
            self.log_conversation(speaker, message)

        else:

            # 2. next speaker sends message
            message = speaker.send()
            speaker.speak(
                self.agents,
                message,
                interruption_callback = self.interruption_callback,
            )
            self.log_conversation(speaker, message)

        # 3. everyone receives message
        for receiver in self.agents:
            receiver.receive(speaker.name, message)

        # 4. increment time
        self.set_speaker_idx(speaker_idx, idx_type="last")
        self._step += 1

        return speaker.name, message
    
    def log_conversation(self, agent: PlantoidDialogueAgent, message: str):
        # print(f"{speaker.name} says: {message}")
        # Log file directory path
        log_dir = os.path.join(os.getcwd(), "logs/conversation_history")

        # Create the directory if it does not exist, do nothing if it exists
        os.makedirs(log_dir, exist_ok=True)

        # Path for the log file
        log_file_path = os.path.join(log_dir, f"interaction_{self.interaction_timestamp}.log")

        formatted_message = agent.think_module.format_response_type(message)

        with open(log_file_path, "a") as f:
            f.write(f"{datetime.now()} - {agent.name} says: {formatted_message}\n")

    def log_agents(self):

        # Log file directory path
        log_dir = os.path.join(os.getcwd(), "logs/conversation_history")

        # Create the directory if it does not exist, do nothing if it exists
        os.makedirs(log_dir, exist_ok=True)

        # Path for the log file
        log_file_path = os.path.join(log_dir, f"interaction_{self.interaction_timestamp}.log")

        attributes = [
            'name', '__class__.__name__', 'is_human', # 'system_message'
            'prefix', 'eleven_voice_id', 'channel_id', # 'bidding_template',
            'tunnel', 'socket', 'callback', 'addr', 'use_model_type',
            'use_streaming', # '__dict__'
        ]

        # Write to the log file
        with open(log_file_path, "w") as f:
            for agent in self.agents:
                for attr in attributes:
                    # Using getattr to check and retrieve the attribute value
                    value = getattr(agent, attr, None)
                    if value is not None:  # Only write if the attribute exists
                        f.write(f"{attr}: {value}\n")
                f.write("\n")
            f.write("========================================\n")
