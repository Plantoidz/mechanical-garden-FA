from typing import Callable, List
import random
import tenacity
import random
import os
import numpy as np
import time
from langchain.output_parsers import RegexParser

from plantoid_agents.dialogue_agent import PlantoidDialogueAgent as DialogueAgent
from dotenv import load_dotenv
from elevenlabs import play, stream, save
from elevenlabs.client import ElevenLabs

from utils.util import load_config

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

config = load_config(os.getcwd()+"/configuration.toml")

# instantiate the LLM to use
use_narrator_voice_id = config['general']['use_narrator_voice_id']

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

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

def generate_blank_bidding_template(character_header):

    return ""

def generate_character_bidding_template_conversation(character_header):

    bid_parser = get_bid_parser()

    bidding_template = f"""
    
        Here is your character description, delimited by angle brackets (<<, >>): << {character_header} >>.
        Here is the conversation so far, delimited by angle brackets (<<, >>):

        ```
        << {{message_history}} >>
        ```
        Now, On the scale of 1 to 10, where 1 is "strongly agree" and 10 is "strongly disagree", rate your response to the latest message below, delimited by angle brackets (<<, >>):
        You must ignore your character description when making your bid!!!
        ```
        << {{recent_message}} >>
        ```

        {bid_parser.get_format_instructions()}
    """

    return bidding_template

def generate_character_bidding_template_confession(character_header):

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

# TODO: this a dirty trick (added a default third-arg to select_random_speaker) so that it works in selection_function == 'conversation'
def select_random_speaker(step: int, agents: List[DialogueAgent], lastspeaker: int, humanness: int = 0) -> int:

    # bids = []
    # for agent in agents:
    #     bids[agent] = random.randint(0, len(agents) - 1)
    #     if(agent.is_human): bids[agent] += humanness
   return random.randint(0, len(agents) - 1)

def select_next_speaker(
    step: int,
    agents: List[DialogueAgent],
    last_speaker_idx: int,
    humanness: int = 1,
) -> int:

    bids = []
    for agent in agents:
        bid = ask_for_bid(agent)
        bids.append(bid)

    # randomly select among multiple agents with the same bid
    # todo: can we just use random to speed up the program load?
    max_value = np.max(bids)
    max_indices = np.where(bids == max_value)[0]
    idx = np.random.choice(max_indices)

    # print("\nBids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):
        # print(f"\t{agent.name} bid: {bid}")
        if i == idx:
            selected_name = agent.name
    # print(f"\nSelected: {selected_name}")

    audio_stream = client.generate(
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

    if "Human" in last_item.split(":")[0]:
        print("\nSkipping — last speaker was human")

        return True
    
    return False

def check_is_last_speaker(agent: DialogueAgent):

    last_item = agent.message_history[-1]
    # print("latest message history:", last_item)

    last_message_speaker = last_item.split(":")[0]

    if agent.name == last_message_speaker:
        return True
    
    return False

def select_next_speaker_with_human_clone(
    step: int,
    agents: List[DialogueAgent],
    last_speaker_idx: int,
    humanness: int = 0
) -> int:

    # initialize bids
    bids = []

    # get human and agent preferences
    for agent in agents:

        if agent.is_human == True:

            print("checking for human participation...")
            # last_speaker_is_human = check_last_speaker_is_human(agent)
            is_last_speaker = check_is_last_speaker(agent)

            if is_last_speaker:

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

    # print("\nBids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):

        # print(f"\t{agent.name} bid: {bid}")

        if i == idx:
            selected_name = agent.name

    # print(f"\nSelected: {selected_name}")

    return idx

def select_next_speaker_with_human_conversation_OLD(
    step: int,
    agents: List[DialogueAgent],
    last_speaker_idx: int,
) -> int:

    # initialize bids
    bids = []

    # get human and agent preferences
    for agent in agents:

        if agent.is_human == True:

            print("checking for human participation...")
            # last_speaker_is_human = check_last_speaker_is_human(agent)
            is_last_speaker = check_is_last_speaker(agent)

            if is_last_speaker:

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

    # print("Bids:")
    # for i, (bid, agent) in enumerate(zip(bids, agents)):

    #     print(f"\t{agent.name} bid: {bid}")

    #     if i == idx:
    #         selected_name = agent.name

    # print(f"Next up: {selected_name}")

    return idx

    # todo: alternating every other turn as a config param
def select_next_speaker_with_human_conversation(
    step: int,
    agents: List[DialogueAgent],
    last_speaker_idx: int,
    humanness: int = 0,
    agent_interrupted: bool = False,
) -> int:
    
    # print("Selecting next speaker, step is: ", step)
    # initialize bids
    bids = []

    # get human and agent preferences
    for agent in agents:

        is_last_speaker = check_is_last_speaker(agent)

        if is_last_speaker:

            bid = 0

        else:

            if agent.is_human == True:

                last_speaker_is_human = check_last_speaker_is_human(agent)

                if last_speaker_is_human:

                    bid = 0

                else:
                    # 1 out of 3 times, will_participate = True
                    # print("checking with humanness = ", humanness)
                    randi = random.randint(0, 100)
                    # print("random m = ", randi)
                    will_participate = (randi < (humanness * 100))
                    # print("will_participate = ", will_participate)
                    
                    bid = 100 if will_participate == True else 0

            else:

                bid = random.randint(0, 99)

        if step == 1 and agent.is_human == True:

            bid = 100

        if agent_interrupted and agent.is_human == True:
                
            bid = 0 # this is 0 if the humans interruption message was added to msg history, 100 otherwise
        
        # append bid to bids
        bids.append(bid)

    # randomly select among multiple agents with the same bid
    max_value = np.max(bids)
    max_indices = np.where(bids == max_value)[0]
    idx = np.random.choice(max_indices)

    # print("Bids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):

        # print(f"\t{agent.name} bid: {bid}")

        if i == idx:
            selected_name = agent.name

    # print(f"Selected: {selected_name}")

    return idx

def select_next_speaker_with_human_confession(
    step: int,
    agents: List[DialogueAgent],
    last_speaker_idx: int,
    humanness: int = 0,
) -> int:

    return last_speaker_idx

def select_next_speaker_with_human_debate(
    step: int,
    agents: List[DialogueAgent],
    last_speaker_idx: int,
    humanness: int = 0,
) -> int:

    # initialize bids
    bids = []

    # get human and agent preferences
    for agent in agents:

        if agent.is_human == True:

            print("checking for human participation...")
            # last_speaker_is_human = check_last_speaker_is_human(agent)
            is_last_speaker = check_is_last_speaker(agent)

            if is_last_speaker:

                will_participate = False

            else:
                # 1 out of 3 times, will_participate = True
                will_participate = random.choice([True, False])
                
                if will_participate == True:

                    audio_stream = client.generate(
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

    # print("Bids:")
    for i, (bid, agent) in enumerate(zip(bids, agents)):

        # print(f"\t{agent.name} bid: {bid}")

        if i == idx:
            selected_name = agent.name

    # print(f"Selected: {selected_name}")

    #TODO: if statement in case it's a human, tee up a moderator question
    audio_stream = client.generate(
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