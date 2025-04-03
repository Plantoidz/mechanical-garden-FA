from typing import Callable, List, Union, Any
from multiprocessing import Queue, Event
from langchain.prompts import PromptTemplate
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent
import os

class PlantoidCloneAgent(PlantoidDialogueAgent):
    def __init__(
        self,
        name: str,
        is_human: bool,
        speech_queue: Queue,
        listen_queue: Queue,
        esp_ws_queue: Queue,
        instruct_queue: Queue,
        speech_event: Event,
        listen_event: Event, 
        system_message: str,
        bidding_template: PromptTemplate,
        # model: Any, # Union[ChatOpenAI, ChatHuggingFace],
        eleven_voice_id: str,
        channel_id: str,
        io: str,
        addr: str,
        esp_id: str,
        local_engine: any = None,
    ) -> None:
        super().__init__(
            name,
            is_human,
            speech_queue,
            listen_queue,
            esp_ws_queue,
            instruct_queue,
            speech_event,
            listen_event, 
            system_message,
            eleven_voice_id,
            channel_id,
            io,
            addr,
            esp_id,
            local_engine=local_engine,
        )
        self.bidding_template = bidding_template
        self.clone_voice = True  # Start with cloning disabled
        self.create_clone = True  # Start with clone creation disabled
        self.has_spoken = False  # Track if agent has spoken
        self.timeout_override_seconds = 5
        self.clone_clip_limit = 5
        self.clone_clip_index = 0

    def speak(self, agents, message: str, use_streaming: bool = True) -> None:
        """
        Speaks the message using the agent's voice
        """
        print("CREATE CLONE: ", self.create_clone)
        print("VOICE ID: ", self.get_voice_id())
        
        # # Enable voice cloning after first speech
        # if self.has_spoken:
        #     self.clone_voice = True
        #     self.create_clone = True

        self.speak_module.speak(
            agents,
            self,
            message,
            self.get_voice_id(),
            self.get_channel_id(),
            voice_set_callback=self.set_create_clone,
            clone_voice=self.clone_voice,
            create_clone=self.create_clone,
            use_streaming = use_streaming,
        )


        if self.clone_clip_index > 0:
            print("CLIP LIMIT REACHED")
            # self.clone_voice = False
            self.has_spoken = True

        self.clone_clip_index += 1


    def set_create_clone(self, voice_id: str) -> None:
        print("CALL SET CREATE CLONE")

        if self.clone_clip_index == 0:

            # Clean up the previous voice clone if it exists
            self.speak_module.cleanup_previous_voice_clone()

            # Save the new voice ID to the file for future cleanup
            voice_clone_file_path = os.path.join(os.getcwd(), "media", "user_audio", "voice_clone_id.txt")
            os.makedirs(os.path.dirname(voice_clone_file_path), exist_ok=True)
            with open(voice_clone_file_path, 'w') as f:
                f.write(voice_id)

        self.eleven_voice_id = voice_id
        self.create_clone = False





    # def listen_for_speech(self, agents, step: int = 0) -> str:
    #     print("Current timeout: ", self.timeout_override_seconds)
    #     print("Current voice id: ", self.get_voice_id())

    #     self.listen_module.play_speech_indicator()
    #     user_message = self.listen_module.listen(self, agents, self.timeout_override_seconds, step=step)

    #     print("\n\033[92m" +"Human said:\033[0m\n" + user_message)

    #     return user_message