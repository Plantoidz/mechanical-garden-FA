from typing import Callable, List, Union
import os

from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models.huggingface import ChatHuggingFace

from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

# import plantoid_agents.lib.speech as PlantoidSpeech
from plantoid_agents.events.listen import Listen
from plantoid_agents.events.speak import Speak
from plantoid_agents.events.think import Think
from plantoid_agents.lib.text_content import *

class PlantoidDialogueAgent:
    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        model: Union[ChatOpenAI, ChatHuggingFace],
        eleven_voice_id: str,
    ) -> None:
        self.name = name
        self.system_message = system_message
        self.model = model
        self.prefix = f"{self.name}: "
        self.reset()

        ### CUSTOM ATTRIBUTES ###
        # eleven voice id
        self.eleven_voice_id = eleven_voice_id
        self.think = Think(model, system_message)
        self.speak = Speak()
        self.listen = Listen()

    def get_voice_id(self) -> str:

        return self.eleven_voice_id

    def reset(self):
        self.message_history = ["Here is the conversation so far."]

    def get_human_participation_preference(self) -> bool:
        
        assert self.name == "Human", "Error: the agent must be the human!"

        # TODO: vocalize
        print("Would you like to speak now? Say only YES or NO")

        user_message = self.listen.listen()

        if "yes" in user_message.lower():
            
            print("The human will speak now...")
            return True
        
        else:
            print("The human will just listen for now...")
            return False


    def listen(self) -> str:

        user_message = self.listen.listen()

        print("Human said: " + user_message)

        return user_message

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """

        # play the background music
        self.speak.play_background_music()

        # generate the message from the langchain model
        print(self.name, 'is thinking about response...')

        use_content = "\n".join(self.message_history + [self.prefix])
        # print("use_content:", use_content)

        # message = self.model(
        #     [
        #         self.system_message,
        #         HumanMessage(content=use_content),
        #     ]
        # )

        message = self.think.think(use_content)

        print(self.name, 'says:')
        print(message)

        # stream audio response
        self.speak.speak(
            message,
            self.get_voice_id(),
            callback=self.speak.stop_background_music,
        )

        return message

    def receive(self, name: str, message: str) -> None:
        """
        Concatenates {message} spoken by {name} into message history
        """
        self.message_history.append(f"{name}: {message}")

#TODO: do not commingle classes and functions here