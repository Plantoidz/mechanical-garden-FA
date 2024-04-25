from typing import Callable, List, Union, Any
import types

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
from litellm import completion, acompletion
from litellm.utils import CustomStreamWrapper
# https://github.com/BerriAI/litellm/blob/main/litellm/utils.py

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

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
        self.llm_config = "gpt-4-turbo" # "ollama_chat/llama3"

    def stream_text(self, response_stream):

        for chunk in response_stream:
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta
                text_chunk = delta.content
                # yield text_chunk
                print(text_chunk, end='', flush=True)

    def gather_response(self, response_stream):
        full_text = ""
        for chunk in response_stream:
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta
                text_chunk = delta.content
                full_text += text_chunk
                print(text_chunk, end='', flush=True)
        return full_text
    
    def format_response_type(self, response: Any) -> Any:
        return response.response_uptil_now if isinstance(response, CustomStreamWrapper) else response

    def generate_bid_template(self, bidding_template, message_history) -> SystemMessage:

        bid_system_message = PromptTemplate(
            input_variables=["recent_message", "message_history"], 
            template=bidding_template,
        ).format(
            message_history="\n".join(message_history),
            recent_message=message_history[-1],
        )

        return SystemMessage(content=bid_system_message)
    
    def think_litellm(self, system_message: SystemMessage, use_content: str):

        messages = [{
            "content": system_message.content,
            "role": "system"
        },
        {
            "content": use_content,
            "role": "user"
        }]

        # print("LITELLM MESSAGE:", messages)

        response_stream = completion(
            model=self.llm_config, 
            messages=messages, 
            stream=True
        )

        # self.stream_text(response_stream)

        return response_stream

    def think_simpleAIChat(self, system_message: SystemMessage, use_content: str) -> str:

        # print("USE CONTENT:", use_content)

        ai_chat = AIChat(
            system=system_message.content,
            api_key=OPENAI_API_KEY,
            model="gpt-4-turbo", # "gpt-3.5-turbo"
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

        if use_model == 'litellm':
            message = self.think_litellm(system_message, use_content)

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