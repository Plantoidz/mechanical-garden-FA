from typing import Callable, List, Union
import tenacity
import os
import numpy as np
from langchain_community.chat_models import ChatLiteLLM, ChatOpenAI
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain_community.llms import HuggingFaceTextGenInference, HuggingFaceEndpoint, HuggingFaceHub
from dotenv import load_dotenv
from utils.util import load_config

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI")
# https://huggingface.co/docs/api-inference/quicktour
LLM_ENDPOINT_URL = "https://hh1j4c263kruj77c.eu-west-1.aws.endpoints.huggingface.cloud"
HF_TOKEN = os.environ.get("HUGGINGFACEHUB_API_TOKEN")

# print("HUGGINGFACEHUB_API_TOKEN", HF_TOKEN)

# TODO: look Into
# python -c "from huggingface_hub.hf_api import HfFolder; HfFolder.save_token('YOUR_TOKEN_HERE')"

def select_llm(interface: str ="openai") -> Union[ChatOpenAI, ChatHuggingFace]:

    if interface == "hf_textgen":

        llm = HuggingFaceTextGenInference(
            inference_server_url=LLM_ENDPOINT_URL,
            max_new_tokens=512,
            top_k=50,
            temperature=0.1,
            repetition_penalty=1.03,
            server_kwargs={
                "headers": {
                    "Authorization": f"Bearer {HF_TOKEN}",
                    "Content-Type": "application/json",
                }
            },
        )

        chat_model = ChatHuggingFace(llm=llm)

    if interface == "hf_endpoint":

        llm = HuggingFaceEndpoint(
            endpoint_url=LLM_ENDPOINT_URL,
            task="text-generation",
            model_kwargs={
                "max_new_tokens": 512,
                "top_k": 50,
                "temperature": 0.1,
                "repetition_penalty": 1.03,
            },
        )

        chat_model = ChatHuggingFace(llm=llm)

    if interface == "hf_hub":

        llm = HuggingFaceHub(
            repo_id="HuggingFaceH4/zephyr-7b-beta",
            task="text-generation",
            model_kwargs={
                "max_new_tokens": 512,
                "top_k": 30,
                "temperature": 0.1,
                "repetition_penalty": 1.03,
            },
        )

        chat_model = ChatHuggingFace(llm=llm)

    if interface == "openai":

        chat_model = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4-turbo", # "gpt-3.5-turbo"
            temperature=0.5,
        )

    return chat_model

def get_llm() -> Union[ChatOpenAI, ChatHuggingFace]:

    config = load_config()

    # instantiate the LLM to use
    use_interface = config['general']['use_llm']
    llm = select_llm(interface=use_interface)

    return llm