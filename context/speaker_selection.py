from typing import Callable, List
import random
import tenacity
import playsound
import random
import os
import numpy as np
from langchain.output_parsers import RegexParser
from langchain.prompts import PromptTemplate
from langchain.schema import (
    HumanMessage,
    SystemMessage,
)

from plantoid_agents.dialogue_agent import PlantoidDialogueAgent as DialogueAgent
from dotenv import load_dotenv
from elevenlabs import generate, stream, set_api_key

from config.scripts.select_llm import get_llm
from utils.util import load_config

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

config = load_config(os.getcwd()+"/configuration.toml")

# instantiate the LLM to use
use_narrator_voice_id = config['general']['use_narrator_voice_id']

#TODO: make class and have this as param
llm = get_llm()

class BidOutputParser(RegexParser):
    
    def get_format_instructions(self) -> str:
         
        instructions = f"""Your response should be an INTENSITY_VALUE, which is integer delimited by angled brackets, like this: <int>.
        This integer should ALWAYS be the ONLY thing you respond with, formatted explicitly as follows: <INTENSITY_VALUE>!!!
        """

        return instructions
    
def get_bid_parser() -> BidOutputParser:

    bid_parser = BidOutputParser(
        regex=r"<(\d+)>", output_keys=["bid"], default_output_key="bid"
    )

    return bid_parser

def generate_character_bidding_template_conversation(character_header):

    bid_parser = get_bid_parser()

    bidding_template = f"""
    
        Here is your character description, delimited by angle brackets (<<, >>): << {character_header} >>.
        Here is the conversation so far, delimited by angle brackets (<<, >>):

        ```
        << {{message_history}} >>
        ```
        Now, On the scale of 1 to 10, where 1 is "strongly agree" and 10 is "strongly disagree", rate your response to the latest message below, delimited by angle brackets (<<, >>):

        ```
        << {{recent_message}} >>
        ```

        {bid_parser.get_format_instructions()}
    """

    return bidding_template

def generate_blank_bidding_template(character_header):

    return ""

def generate_character_bidding_template_debate(character_header):
            
    bid_parser = get_bid_parser()

    bidding_template = f"""
    
        Here is your character description, delimited by angle brackets (<<, >>): << {character_header} >>.
        Here is the debate so far, delimited by angle brackets (<<, >>):

        ```
        << {{message_history}} >>
        ```
        Now, On the scale of 1 to 10, where 1 is "strongly agree" and 10 is "strongly disagree", rate your response to the latest message below, delimited by angle brackets (<<, >>):

        ```
        << {{recent_message}} >>
        ```

        {bid_parser.get_format_instructions()}
    """

    return bidding_template

def mock_select_speaker(step: int, agents: List[DialogueAgent]) -> int:

    return 0

def select_random_speaker(step: int, agents: List[DialogueAgent]) -> int:

    return random.randint(0, len(agents) - 1)

def select_next_speaker(step: int, agents: List[DialogueAgent]) -> int:

    bids = []
    for agent in agents:
        bid = ask_for_bid(agent)
        bids.append(bid)

    # randomly select among multiple agents with the same bid
    max_value = np.max(bids)
    max_indices = np.where(bids == max_value)[0]
    idx = np.random.choice(max_indices)

    print("Bids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):
        print(f"\t{agent.name} bid: {bid}")
        if i == idx:
            selected_name = agent.name
    print(f"Selected: {selected_name}")

    audio_stream = generate(
            text=f"{selected_name}?",
            model="eleven_turbo_v2",
            voice=use_narrator_voice_id,
            stream=True
        )
    
    stream(audio_stream)
    print("\n")
    return idx

def check_last_speaker_is_human(agent: DialogueAgent):

    last_item = agent.message_history[-1]
    # print("latest message history:", last_item)

    if last_item.split(":")[0] == "Human":
        print("Last speaker was human")

        return True
    
    return False

def select_next_speaker_with_human_clone(
    step: int,
    agents: List[DialogueAgent],
) -> int:

    # initialize bids
    bids = []

    # get human and agent preferences
    for agent in agents:

        if agent.name == "Human":

            print("checking for human participation...")
            last_speaker_is_human = check_last_speaker_is_human(agent)

            if last_speaker_is_human:

                will_participate = False

            else:
                # 1 out of 3 times, will_participate = True
                will_participate = True

            # hacky to be max bid of 100, to be fixed or added to config file
            bid = 100 if will_participate else 0

        else:

            last_speaker = agent.message_history[-1].split(":")[0]

            # do not make the same agent speak twice in a row
            if agent.name == last_speaker:

                bid = 0

            else:

                bid = 10
        
        # append bid to bids
        bids.append(bid)

    # randomly select among multiple agents with the same bid
    max_value = np.max(bids)
    max_indices = np.where(bids == max_value)[0]
    idx = np.random.choice(max_indices)

    print("Bids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):

        print(f"\t{agent.name} bid: {bid}")

        if i == idx:
            selected_name = agent.name

    print(f"Selected: {selected_name}")

    return idx

def select_next_speaker_with_human_conversation(
    step: int,
    agents: List[DialogueAgent],
) -> int:

    # initialize bids
    bids = []

    # get human and agent preferences
    for agent in agents:

        if agent.name == "Human":

            print("checking for human participation...")
            last_speaker_is_human = check_last_speaker_is_human(agent)

            if last_speaker_is_human:

                will_participate = False

            else:
                # 1 out of 3 times, will_participate = True
                will_participate = True

            # hacky to be max bid of 100, to be fixed or added to config file
            bid = 100 if will_participate else 0

        else:

            last_speaker = agent.message_history[-1].split(":")[0]

            # do not make the same agent speak twice in a row
            if agent.name == last_speaker:

                bid = 0

            else:

                bid = ask_for_bid(agent)
        
        # append bid to bids
        bids.append(bid)

    # randomly select among multiple agents with the same bid
    max_value = np.max(bids)
    max_indices = np.where(bids == max_value)[0]
    idx = np.random.choice(max_indices)

    print("Bids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):

        print(f"\t{agent.name} bid: {bid}")

        if i == idx:
            selected_name = agent.name

    print(f"Selected: {selected_name}")

    return idx

def select_next_speaker_with_human_debate(
    step: int,
    agents: List[DialogueAgent],
) -> int:

    # initialize bids
    bids = []

    # get human and agent preferences
    for agent in agents:

        if agent.name == "Human":

            print("checking for human participation...")
            last_speaker_is_human = check_last_speaker_is_human(agent)

            if last_speaker_is_human:

                will_participate = False

            else:
                # 1 out of 3 times, will_participate = True
                will_participate = random.choice([True, False])
                
                if will_participate == True:

                    audio_stream = generate(
                        text=f"Prepare to weigh in.",
                        model="eleven_turbo_v2",
                        voice=use_narrator_voice_id,
                        stream=True
                    )

                    print("Prepare to weigh in.")
                    stream(audio_stream)

            # hacky to be max bid of 100, to be fixed or added to config file
            bid = 100 if will_participate else 0

        else:

            last_speaker = agent.message_history[-1].split(":")[0]

            # do not make the same agent speak twice in a row
            if agent.name == last_speaker:

                bid = 0

            else:

                bid = ask_for_bid(agent)
        
        # append bid to bids
        bids.append(bid)

    # randomly select among multiple agents with the same bid
    max_value = np.max(bids)
    max_indices = np.where(bids == max_value)[0]
    idx = np.random.choice(max_indices)

    print("Bids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):

        print(f"\t{agent.name} bid: {bid}")

        if i == idx:
            selected_name = agent.name

    print(f"Selected: {selected_name}")

    #TODO: if statement in case it's a human, tee up a moderator question
    audio_stream = generate(
            text=f"{selected_name}?",
            model="eleven_turbo_v2",
            voice=use_narrator_voice_id,
            stream=True
        )
    
    stream(audio_stream)
    print("\n")

    return idx

@tenacity.retry(
    stop=tenacity.stop_after_attempt(2),
    wait=tenacity.wait_none(),  # No waiting time between retries
    retry=tenacity.retry_if_exception_type(ValueError),
    before_sleep=lambda retry_state: print(
        f"ValueError occurred: {retry_state.outcome.exception()}, retrying..."
    ),
    retry_error_callback=lambda retry_state: 0,
)  # Default value when all retries are exhausted
def ask_for_bid(agent) -> str:
    """
    Ask for agent bid and parses the bid into the correct format.
    """
    bid_parser = get_bid_parser()
    bid_string = agent.bid()
    bid = int(bid_parser.parse(bid_string)["bid"])
    return bid