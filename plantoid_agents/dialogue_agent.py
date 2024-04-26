from typing import Callable, List, Union
import os

from langchain_openai import ChatOpenAI
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

BLUE = '\033[94m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
ENDC = '\033[0m'

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
        self.think_module = Think(model)
        self.speak_module = Speak()
        self.listen_module = Listen()

        #TODO: do not hardcode!
        self.use_model_type = "langchain"

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
            
            print(GREEN + "The human will speak now..." + ENDC)
            return True
        
        else:
            print(GREEN + "The human will just listen for now..." + ENDC)
            return False


    def listen_for_speech(self) -> str:

        self.listen_module.play_speech_indicator()
        user_message = self.listen_module.listen()

        print("Human said: " + user_message)

        return user_message

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """

        # play the background music
        # self.speak_module.play_background_music()

        # generate the message from the langchain model
        print(BLUE + "\n" + self.name + ' is thinking about response...' + ENDC)

        self.message_history = self.clip_history(self.message_history, n_messages=5)

        use_content = "\n".join(self.message_history + [self.prefix])
        # print("use_content:", use_content)

        print("\n\t" + BLUE + "AGENT:" + ENDC, self.name)
        # todo: just print raw system message
        print("\n\t" + BLUE + "SYSTEM MESSAGE:" + ENDC, "{self.system_message}")
        print("\n\t" + BLUE + "MESSAGE HISTORY:" + ENDC, self.message_history)

        message = self.think_module.think(
            self.system_message,
            use_content,
            self.use_model_type,
        )

        print("\n" + BLUE + self.name, 'says:' + ENDC)
        print(GREEN + message + ENDC +"\n")

        return message
    
    def speak(self, message: str) -> None:
        """
        Speaks the message using the agent's voice
        """

        self.speak_module.stop_background_music()
        
        self.speak_module.speak(
            message,
            self.get_voice_id(),
            callback=None, #self.speak_module.stop_background_music,
        )

    def receive(self, name: str, message: str) -> None:
        """
        Concatenates {message} spoken by {name} into message history
        """
        self.message_history.append(f"{name}: {message}")

    def clip_history(self, lst, n_messages=5):
        """
        Clips the history to the last n messages
        """
        if len(lst) == 0:
            return []  # Return an empty list if the input list is empty
        
        return [lst[0]] + lst[-n_messages:] if len(lst) > n_messages else lst

#TODO: do not commingle classes and functions here