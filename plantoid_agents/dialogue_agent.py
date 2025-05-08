from typing import Callable, List, Union
import socket
from litellm.utils import CustomStreamWrapper

# import plantoid_agents.lib.speech as PlantoidSpeech
from plantoid_agents.tools.listen import Listen
from plantoid_agents.tools.speak import Speak
from plantoid_agents.tools.think import Think
from plantoid_agents.lib.text_content import *
from plantoid_agents.modules.serial_socket.serial_socket import SerialSocket
from plantoid_agents.modules.resolume_osc.resolume_osc import ResolumeOSC

# TEMP
from litellm.utils import CustomStreamWrapper

PURPLE = '\033[94m'
BLUE = '\033[34m'
GREY = '\033[90m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
ENDC = '\033[0m'

class PlantoidDialogueAgent:
    def __init__(
        self,
        name: str,
        is_human: bool,
        system_message: str,
        # model: Union[ChatOpenAI, ChatHuggingFace],
        eleven_voice_id: str,
        channel_id: str,
        io: str,
        addr: str,
        resolume_ip: str = "192.168.1.159",
        resolume_port: int = 7000,
    ) -> None:
        """
        Initialize a PlantoidDialogueAgent.
        
        Args:
            name (str): Name of the agent
            is_human (bool): Whether this agent represents a human
            system_message (str): System message for the agent
            eleven_voice_id (str): Voice ID for ElevenLabs
            channel_id (str): Channel ID for audio
            io (str): IO type ('wifi' or other)
            addr (str): Address for communication
            resolume_ip (str): IP address for Resolume OSC
            resolume_port (int): Port for Resolume OSC
        """
        self.name = name
        self.is_human = is_human
        self.system_message = system_message
        # self.model = model
        self.prefix = f"{self.name}: "
        self.reset()

        ### CUSTOM ATTRIBUTES ###
        # eleven voice id
        self.eleven_voice_id = eleven_voice_id
        self.think_module = Think()
        self.speak_module = Speak()
        self.listen_module = Listen()
        self.channel_id = channel_id
        
        self.serial_socket = None
        self.resolume_osc = None
        self.callback = None
        if io == "wifi" and addr:
            print(f"Connecting to Plantoid IP: {addr}")
            self.serial_socket = SerialSocket(addr)
            self.resolume_osc = ResolumeOSC(ip=resolume_ip, port=resolume_port)
            self.callback = self._handle_callback

        #TODO: do not hardcode!
        # self.use_model_type = "litellm"
        self.use_streaming = True
        self.stream_transcript = ""

    def _handle_callback(self, message: str) -> None:
        """
        Handle callback messages by sending them through both serial socket and OSC.
        
        Args:
            message (str): Message to send
        """
        # Send serial message
        if self.serial_socket:
            self.serial_socket.send_message(message)
        
        # Send OSC message based on the state
        if self.resolume_osc:
            state = message.strip("<>")  # Remove < > from the message
            self.resolume_osc.set_ai_state(state)

    def get_voice_id(self) -> str:
        """Get the ElevenLabs voice ID."""
        return self.eleven_voice_id
    
    def get_channel_id(self) -> int:
        """Get the channel ID."""
        return self.channel_id

    def reset(self):
        """Reset the message history."""
        self.message_history = []
        # self.message_history = ["Someone should kick off the discussion."]

    def get_human_participation_preference(self) -> bool:
        """
        Get the human's preference for participation.
        
        Returns:
            bool: True if human wants to speak, False otherwise
        """
        assert self.name == "Human", "Error: the agent must be the human!"

        # TODO: vocalize
        print("Would you like to speak now? Say only YES or NO")

        user_message = self.listen_module.listen()

        if "yes" in user_message.lower():
            
            print(GREEN + "The human will speak now..." + ENDC)
            return True
        
        else:
            print(GREEN + "The human will just listen for now..." + ENDC)
            return False

    def listen_for_speech(self, agents, step: int = 0) -> str:
        """
        Listen for speech input.
        
        Args:
            agents: List of agents
            step (int): Current step in the conversation
            
        Returns:
            str: Recognized speech text
        """
        self.listen_module.play_speech_indicator()
        user_message = self.listen_module.listen(agents, step=step)

        if user_message is None:
            print("\n\033[93mNo speech detected or recognition failed.\033[0m")
            return ""
            
        print("\n\033[92m" + "Human said:\033[0m\n" + user_message)
        return user_message

    def send(self) -> str:
        """
        Generate a response based on the message history.
        
        Returns:
            str: Generated response message
        """
        # play the background music
        # self.speak_module.play_background_music()

        print("\n\n" + PURPLE + self.name + ' is thinking...' + ENDC)

        self.message_history = self.clip_history(self.message_history, n_messages=5)

        use_content = "\n".join(self.message_history + [self.prefix])
        # print("use_content:", use_content)

        # print("AGENT:", self.name)
        print("" + GREY + "Character description:", self.system_message, ENDC)
        # print("MESSAGE HISTORY:", self.message_history)
        # print("\n\t" + BLUE + "AGENT:" + ENDC, self.name)
        # todo: just print raw system message
        # print("\n\t" + BLUE + "SYSTEM MESSAGE:" + ENDC, self.system_message)
        print("\n" + GREY + "Message history:", self.message_history, ENDC)

        self.listen_module.play_speech_acknowledgement(self.get_voice_id())

        message = self.think_module.think(
            self,
            self.system_message,
            use_content,
            # self.use_model_type,
            self.use_streaming,
        )

        print("\n" + PURPLE + self.name, 'says:' + ENDC)

        return message
    
    def speak(
        self,
        agents,
        message: str,
        use_streaming: bool = True,
        clone_voice: bool = False,
        create_clone: bool = False,
        interruption_callback: Callable = None,
    ) -> None:
        """
        Speak the message using the agent's voice.
        
        Args:
            agents: List of agents
            message (str): Message to speak
            use_streaming (bool): Whether to use streaming
            clone_voice (bool): Whether to clone voice
            create_clone (bool): Whether to create voice clone
            interruption_callback (Callable): Callback for interruptions
        """
        
        # TODO: re-enable backgroud stop
        # self.speak_module.stop_background_music()
        # use_streaming = False
        # print("message ========= ", message)
        # print("speak(1): use streaming = ", use_streaming)

        self.speak_module.speak(
            agents,
            self,
            message,
            self.get_voice_id(),
            self.get_channel_id(),
            # bg_callback=None, #self.speak_module.stop_background_music,
            interruption_callback = interruption_callback,
            use_streaming = use_streaming,
            clone_voice = clone_voice,
            create_clone = create_clone,
        )

        return self.stream_transcript

    
    def receive(self, name: str, message: Union[str, CustomStreamWrapper]) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            name (str): Name of the speaker
            message (Union[str, CustomStreamWrapper]): Message content
        """
        # NOTE: stream data is not available to stringify until after speech
        # generator has not iterated before this point!
        # formatted_message = self.speak_module.format_response_type(message)

        # print(self.name, 'says:')
        # print(formatted_message)

        self.message_history.append(f"{name}: {message}")

    def clip_history(self, lst, n_messages=5):
        """
        Clips the history to the last n messages
        """
        if len(lst) == 0:
            return []  # Return an empty list if the input list is empty
        
        return [lst[0]] + lst[-n_messages:] if len(lst) > n_messages else lst

#TODO: do not commingle classes and functions here