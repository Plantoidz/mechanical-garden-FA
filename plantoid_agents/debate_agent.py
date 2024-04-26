from typing import Callable, List, Union
from langchain_community.chat_models import ChatOpenAI
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain.prompts import PromptTemplate
from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

from plantoid_agents.dialogue_agent import PlantoidDialogueAgent

class PlantoidDebateAgent(PlantoidDialogueAgent):
    def __init__(
        self,
        name,
        system_message: SystemMessage,
        bidding_template: PromptTemplate,
        model: Union[ChatOpenAI, ChatHuggingFace],
        eleven_voice_id: str,
    ) -> None:
        super().__init__(name, system_message, model, eleven_voice_id)
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

        use_content = "Your response should be an integer delimited by angled brackets, like this: <int>"

        bid_string = self.think_module.think(
            bid_system_message,
            use_content,
            self.use_model_type,
        )

        return bid_string