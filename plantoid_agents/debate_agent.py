from typing import Callable, List, Union, Any
from multiprocessing import Queue, Event
from plantoid_agents.dialogue_agent import PlantoidDialogueAgent

class PlantoidDebateAgent(PlantoidDialogueAgent):
    def __init__(
        self,
        name: str,
        is_human: bool,
        speech_queue: Queue,
        listen_queue: Queue,
        speech_event: Event,
        listen_event: Event,
        system_message: str,
        bidding_template: str,
        # model: Any, #Union[ChatOpenAI, ChatHuggingFace],
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

    def bid(self) -> str:
        """
        Asks the chat model to output a bid to speak
        """
        bid_system_message = self.think_module.generate_bid_template(
            self.bidding_template,
            self.message_history, # self.clip_history(self.message_history, n_messages=1),
        )

        # print("BID SYSTEM MESSAGE:", bid_system_message)

        use_content = "Ignore your character description. Your response should be an integer delimited by angled brackets, like this: <int>"

        use_streaming = False

        # print("BID SYSTEM MESSAGE:", bid_system_message)

        bid_string = self.think_module.think(
            self,
            bid_system_message,
            use_content,
            self.use_model_type,
            use_streaming,
        )

        return bid_string