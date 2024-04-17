from typing import Callable, List, Union

from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models.huggingface import ChatHuggingFace

from langchain.output_parsers import RegexParser
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
        prompt = PromptTemplate(
            input_variables=["message_history", "recent_message"],
            template=self.bidding_template,
        ).format(
            message_history="\n".join(self.message_history),
            recent_message=self.message_history[-1],
        )

        # TODO: tbc move this functionality to characters.py and just call it here
        # print("Bid prompt is:", prompt)

        # bid_string = self.model([SystemMessage(content=prompt)]).content

        bid_resolution_prompt = [
            SystemMessage(content=prompt),
            HumanMessage(content="Your response should be an integer delimited by angled brackets, like this: <int>"),
        ]

        bid_string = self.model(bid_resolution_prompt).content
        # print("Bid string is:", bid_string)

        return bid_string