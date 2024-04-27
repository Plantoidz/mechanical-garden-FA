from typing import Callable, List, Union

from langchain_openai import ChatOpenAI
from langchain_community.chat_models.huggingface import ChatHuggingFace

from langchain.output_parsers import RegexParser
from langchain.prompts import PromptTemplate
from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

from plantoid_agents.dialogue_agent import PlantoidDialogueAgent

class PlantoidCloneAgent(PlantoidDialogueAgent):
    def __init__(
        self,
        name,
        system_message: SystemMessage,
        bidding_template: PromptTemplate,
        model: Union[ChatOpenAI, ChatHuggingFace],
        eleven_voice_id: str,
        channel_id: str,
    ) -> None:
        super().__init__(name, system_message, model, eleven_voice_id, channel_id)
        self.bidding_template = bidding_template
        self.clone_voice = False
        self.create_clone = False
        self.timeout_override_seconds = 5

    def listen_for_speech(self) -> str:

        print("Current timeout: ", self.timeout_override_seconds)
        print("Current voice id: ", self.get_voice_id())

        self.listen_module.play_speech_indicator()
        user_message = self.listen_module.listen(self.timeout_override_seconds)

        print("Human said: " + user_message)

        return user_message

    def speak(self, message: str) -> None:
        """
        Speaks the message using the agent's voice
        """

        self.speak_module.stop_background_music()

        self.speak_module.speak(
            message,
            self.get_voice_id(),
            voice_set_callback=None,
            clone_voice=self.clone_voice,
            create_clone=self.create_clone,
        )

        # if self.create_clone == False:
        #     self.timeout_override_seconds = 5
        # print("CREATE CLONE: ", self.create_clone)
        # print("VOICE ID: ", self.get_voice_id())

    def set_create_clone(self, voice_id: str) -> None:
        print("CALL SET CREATE CLONE")
        self.create_clone = False
        self.eleven_voice_id = voice_id
        # self.timeout_override_seconds = 5

