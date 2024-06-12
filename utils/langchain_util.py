import os
from typing import Callable, List

from dotenv import load_dotenv
from config.scripts.select_llm import get_llm
from utils.util import load_config

# Load environment variables from .env file
load_dotenv()

config = load_config()


OPENAI_API_KEY = os.environ.get("OPENAI")
ELEVENLABS_API_KEY = os.environ.get("ELEVEN")

# instantiate the LLM to use
use_interface = config['general']['use_llm']
llm = get_llm(interface=use_interface)
