from typing import Callable, List, Union
from multiprocessing import Queue, Event, get_context
import asyncio
import socket

# import plantoid_agents.lib.speech as PlantoidSpeech
from plantoid_agents.events.listen import Listen
from plantoid_agents.events.speak import Speak
from plantoid_agents.events.think import Think
from plantoid_agents.lib.text_content import *

# TEMP
from litellm.utils import CustomStreamWrapper
import threading
import time

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
        speech_queue: Queue,
        listen_queue: Queue,
        esp_ws_queue: Queue,
        instruct_queue: Queue,
        speech_event: Event,
        listen_event: Event, 
        system_message: str,
        # model: Union[ChatOpenAI, ChatHuggingFace],
        eleven_voice_id: str,
        channel_id: str,
        io: str,
        addr: str,
        esp_id: str,
        local_engine: any = None,
    ) -> None:
        # self.ctx = get_context('spawn')
        # self.speech_queue = self.ctx.Queue()
        # self.listen_queue = self.ctx.Queue()
        self.local_engine = local_engine
        self.speech_queue = speech_queue
        self.listen_queue = listen_queue
        self.esp_ws_queue = esp_ws_queue
        self.instruct_queue = instruct_queue
        self.speech_event = speech_event
        self.listen_event = listen_event
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
        self.speak_module = Speak(local_engine=self.local_engine)
        self.listen_module = Listen()
        self.channel_id = channel_id
        
        self.tunnel = None
        self.callback = None
        self.socket = None
        self.esp_id = esp_id

        if(io == "wifi" and addr):
            print("connecting to Plantoid IP: ", addr)
            try:
                # self.tunnel = Telnet(addr, 23, timeout=3)
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.callback = self.tunnel_wifi
                self.addr = addr
            except Exception as err:
                print("Failed to connect: ", err)
                
        elif(io == "ws" and esp_id):
            self.callback = self.tunnel_ws

        #TODO: do not hardcode!
        # self.use_model_type = "litellm"
        self.use_streaming = True

        # Start a thread to check the queue for matching esp_id
        # self.register_esp_thread = threading.Thread(target=self.associate_esp_websocket)
        # self.register_esp_thread.start()

    def set_esp_id(self, esp_id):
        self.esp_id = esp_id

        

    def tunnel_wifi(self, val):
    #     if(not self.tunnel):
    #        if(self.io and self.addr):
    #         try:
    #                 self.tunnel = Telnet(self.addr, 23, timeout=3)
    #                 self.callback = self.tunnel_wifi
    #         except Exception as err:
    #                 print("Failed to connect: ", err)

    #     if(self.tunnel): self.tunnel.write(val.encode('ascii') + b"\n")
        if(self.socket): 
            try: 
                self.socket.sendto(bytes(val, 'utf-8'), (self.addr, 666))
            except Exception as err:
                print("Failed to connect to", self.addr, "with error:", err)

    def tunnel_serial(self, val):
        return ## TODO, activate the serial communication
    
    def tunnel_ws(self, val):
        print("inside the tunnel................. value ===================== ", val, " for agent = ", self.esp_id)
        if(val == "<speaking>"): return # we are handling this directly via the server
        if(val == "<thinking>"): # add instruction to the queue
            # instruct the ESP to playback 
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.instruct_queue.put_nowait, (self.esp_id, "2")) # thinking
        if(val == "<listening>"): 
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.instruct_queue.put_nowait, (self.esp_id, "1")) # listening
        if(val == "<asleep>"):
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.instruct_queue.put_nowait, (self.esp_id, "0")) # idle
    

    def associate_esp_websocket(self):
        # self.socket = ws
        # print("ASSOCIATE ESP WEBSOCKET", self.channel_id, esp_id, self.channel_id == esp_id)
        while True:
            esp_id = int(self.esp_ws_queue.get())

            if esp_id == self.channel_id:
                print(f"Agent {self.name} found matching ESP ID: {esp_id}")
                self.set_esp_id(esp_id)
                time.sleep(1)
            # esp_id, ws = self.esp_ws_queue.get()
            # if esp_id == self.channel_id:
            #     print(f"Agent {self.name} found matching ESP ID: {esp_id}")
            #     # Do something with the matching esp_id
            #     self.socket = ws
            # time.sleep(1)


    def get_voice_id(self) -> str:

        return self.eleven_voice_id
    
    def get_channel_id(self) -> int:
        
        return self.channel_id

    def reset(self):
        self.message_history = []
        # self.message_history = ["Someone should kick off the discussion."]

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


    def listen_for_speech(self, agents, step: int = 0, non_human_agent = None) -> str:

        self.listen_module.play_speech_indicator(non_human_agent)
        user_message = self.listen_module.listen(agents,  non_human_agent, step=step)

        print("\n\033[92m" +"Human said:\033[0m\n" + user_message)

        return user_message

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
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
        # formatted_message = self.think_module.format_response_type(message)
        # print(formatted_message)

        return message
    
    def play(self, filename: str, streaming: bool = True) -> None:
        self.speak_module.play(self, filename, streaming)

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
        Speaks the message using the agent's voice
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
    
    def receive(self, name: str, message: Union[str, CustomStreamWrapper]) -> None:

        """
        Concatenates {message} spoken by {name} into message history
        """
        # NOTE: stream data is not available to stringify until after speech
        # generator has not iterated before this point!
        formatted_message = self.think_module.format_response_type(message)

        # print(self.name, 'says:')
        # print(formatted_message)

        self.message_history.append(f"{name}: {formatted_message}")

    def clip_history(self, lst, n_messages=5):
        """
        Clips the history to the last n messages
        """
        if len(lst) == 0:
            return []  # Return an empty list if the input list is empty
        
        return [lst[0]] + lst[-n_messages:] if len(lst) > n_messages else lst

#TODO: do not commingle classes and functions here