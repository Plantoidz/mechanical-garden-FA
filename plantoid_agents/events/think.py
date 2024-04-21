from typing import Callable, List, Union

import openai
import os

from dotenv import load_dotenv

from config.scripts.default_prompt_config import default_chat_completion_config, default_completion_config
from utils.util import load_config, str_to_bool


from langchain.chat_models import ChatOpenAI
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain.output_parsers import RegexParser
from langchain.prompts import PromptTemplate

from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

from simpleaichat import AsyncAIChat, AIChat

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class Think:
    """
    A template class for implementing cognitive behaviors in an interaction system.
    """

    def __init__(
        self,
        model: Union[ChatOpenAI, ChatHuggingFace],
        # system_message: SystemMessage,
    ):
        """
        Initializes a new instance of the Think class.
        """
        self.model = model

    def generate_bid_template(self, bidding_template, message_history) -> SystemMessage:

        bid_system_message = PromptTemplate(
            input_variables=["recent_message", "message_history"], 
            template=bidding_template,
        ).format(
            message_history="\n".join(message_history),
            recent_message=message_history[-1],
        )

        return SystemMessage(content=bid_system_message)

    def think_simpleAIChat(self, system_message: SystemMessage, use_content: str) -> str:

        # print("USE CONTENT:", use_content)

        ai_chat = AIChat(
            system=system_message.content,
            api_key=OPENAI_API_KEY,
            model="gpt-4-turbo",
            console=False,
            params = {"temperature": 0.5}#, "max_tokens": 3}
        )

        message = ai_chat(use_content)
        
        return message

    def think_langchain(self, system_message: SystemMessage, use_content: str) -> str:
        
        message = self.model(
            [
                system_message,
                HumanMessage(content=use_content),
            ]
        )

        return message.content
    
    def think(self, system_message: SystemMessage, use_content: str, use_model: str) -> str:
            
        if use_model == 'simpleAIChat':
            message = self.think_simpleAIChat(system_message, use_content)

        if use_model == 'langchain':
            message = self.think_langchain(system_message, use_content)

        return message

    def GPTmagic_manual(self, prompt, call_type='chat_completion') -> str: 

        # allowable kwargs
        allowable_call_types = ['chat_completion', 'completion']

        assert call_type in allowable_call_types, "The provided call type is not implemented"

        if call_type == 'chat_completion':

            # Prepare the GPT magic
            config = default_chat_completion_config(model="gpt-4")

            # Generate the response from the GPT model
            response = openai.ChatCompletion.create(messages=[{
                "role": "user",
                "content": prompt,
            }], **config)

            message = response.choices[0].message.content
            print('gpt response:', message)

            return message
        
        if call_type == 'completion':
            # # The GPT-3.5 model ID you want to use
            # model_id = "text-davinci-003"

            # # The maximum number of tokens to generate in the response
            # max_tokens = 1024

            config = default_completion_config()

            # Generate the response from the GPT-3.5 model
            response = openai.Completion.create(
                prompt=prompt,
                **config,
            )

            return response