from typing import Callable, List, Union, Any
from multiprocessing import Queue, Event
from langchain.prompts import PromptTemplate
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent

class PlantoidCloneAgent(PlantoidDialogueAgent):
    def __init__(
        self,
        name: str,
        is_human: bool,
        speech_queue: Queue,
        listen_queue: Queue,
        esp_ws_queue: Queue,
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
    ) -> None:
        super().__init__(
            name,
            is_human,
            speech_queue,
            listen_queue,
            esp_ws_queue,
            speech_event,
            listen_event, 
            system_message,
            eleven_voice_id,
            channel_id,
            io,
            addr,
            esp_id,
        )
        self.bidding_template = bidding_template
        self.clone_voice = True
        self.create_clone = True
        self.timeout_override_seconds = 5
        self.clone_from_single_clip = True

    def speak(self, agents, message: str, use_streaming: bool = True) -> None:
        """
        Speaks the message using the agent's voice
        """
        print("CREATE CLONE: ", self.create_clone)
        print("VOICE ID: ", self.get_voice_id())
        
        # self.speak_module.stop_background_music()

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

        # if self.create_clone == False:
        #     self.timeout_override_seconds = 5


    def set_create_clone(self, voice_id: str) -> None:
        print("CALL SET CREATE CLONE")
        self.create_clone = False
        self.eleven_voice_id = voice_id
        # self.timeout_override_seconds = 5

        if self.clone_from_single_clip:
            self.clone_voice = False


    # def listen_for_speech(self, agents, step: int = 0) -> str:
    #     print("Current timeout: ", self.timeout_override_seconds)
    #     print("Current voice id: ", self.get_voice_id())

    #     self.listen_module.play_speech_indicator()
    #     user_message = self.listen_module.listen(self, agents, self.timeout_override_seconds, step=step)

    #     print("\n\033[92m" +"Human said:\033[0m\n" + user_message)

    #     return user_message