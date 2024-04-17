from typing import Callable, List
import random
import tenacity
import playsound
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

OPENAI_API_KEY = os.environ.get("OPENAI")
ELEVENLABS_API_KEY = os.environ.get("ELEVEN")

config = load_config(os.getcwd()+"/configuration.toml")

# instantiate the LLM to use
use_interface = config['general']['use_llm']
use_narrator_voice_id = config['general']['use_narrator_voice_id']
llm = get_llm(interface=use_interface)

class BidOutputParser(RegexParser):
    
    def get_format_instructions(self) -> str:
         
        instructions = f"""Your response should be an integer delimited by angled brackets, like this: <int>.
        This integer should ALWAYS be the ONLY thing you respond with, like this: <int> !
        Never reply with anything but an integer delimited by angled brackets, like this: <int> !!!
        """

        return instructions
    
def get_bid_parser() -> BidOutputParser:

    bid_parser = BidOutputParser(
        regex=r"<(\d+)>", output_keys=["bid"], default_output_key="bid"
    )

    return bid_parser

def specify_topic_from_prompt(
    game_description,
    word_limit,
    character_names,
):
    
    # content = f"""{game_description}
            
    #     You are an evil debate moderator.
    #     Help us make the debate topic more specific. 
    #     Do not shy away from controversy. We like to shock and polarize people.
    #     Keep it brief and simple.
    #     Please reply with the specified topic in {word_limit} words or less. 
    #     Name the participants in the debate: {*character_names,}.
    #     Conclude by asking for an opening statement.
    # """

    content = f"""{game_description}
            
        You are an evil debate moderator.
        You must make the debate topic more specific. 
        Do not shy away from controversy. We like to shock and polarize people.
        If the topic of debate is binary you must not generalize it, encourage participants to take sides!
        Keep your reply to a single sentence.
        Your reply should always be able to be spoken out loud.
        Avoid colons in your reply.
        Please reply with the specified topic in {str(3 * int(word_limit))} words or less. 
    """

    topic_specifier_prompt = [
        SystemMessage(content="You can make a task more specific."),
        HumanMessage(content=content),
    ]

    specified_topic = llm(topic_specifier_prompt).content

    return specified_topic

def specify_participants(
    specific_game_description,
    word_limit,
    character_names,
):
    
    content = f"""You are given this specific description: {specific_game_description}
        You are an evil debate moderator which must now introduce the participants in context.
        Name the participants in the debate: {*character_names[1:],}.
        Conclude by asking for an opening statement.
        Keep the description of each participant tp a maximum of {word_limit} words!
        Keep the opening statement to a maximum of {str(int(0.5 * int(word_limit)))} words!
        Always begin the output by saying, "Now, the participants in this debate are:"
    """

    topic_specifier_prompt = [
        SystemMessage(content="You can describe participants in context."),
        HumanMessage(content=content),
    ]

    specified_topic = llm(topic_specifier_prompt).content

    return specified_topic

def generate_character_description(
    character_name,
    character_short_description,
    game_description,
    player_descriptor_system_message,
    word_limit,
):

    if character_name == "Human":

        character_description = f"""
            The real person, not a simulated person.
        """
    
    else:

        message_content = f"""{game_description}
            You are {character_name}, speak in {word_limit} words or less! 
            Speak directly to {character_name}.
            Speak only from your own perspective!
            Your behavioral description is: {character_short_description}.
            Be poignant, aggressive, and use swear words if you need to get a point across!
            Keep everything you say to a strict maximum of {word_limit} words.
            Do not add anything else.
        """

        character_specifier_prompt = [
            player_descriptor_system_message,
            HumanMessage(content=message_content),
        ]

        # print('character_specifier_prompt', character_specifier_prompt)

        # character_description = ChatOpenAI(
        #     openai_api_key=OPENAI_API_KEY,
        #     temperature=1.0,
        # )(
        #     character_specifier_prompt
        # ).content

        character_description = llm(
            character_specifier_prompt
        ).content

    return character_description


def generate_character_header(
    game_description,
    topic,
    character_name,
    character_description,
    word_limit,
):

    if character_name == "Human":

        response = f"""I am a human which will listen to and speak with the plantoids."""

    else:
        # response = f"""{game_description}
        #     Your name is {character_name}.
        #     Your description is as follows: {character_description}
        #     You are debating the topic: {topic}.
        #     You must state your true opinion, but make sure to consider what the others are thinking.
        #     You may be convinced to change your mind if you are presented with a convincing argument.
        #     If you change your mind, be explicit about it.
        #     If you change your mind, motivate why your opinion changed.
        #     You must keep all of your responses {word_limit} words!
        # """
        
        response = f"""{game_description}
            
            Your character description: {character_description}
            Always adhere to your character description, be poignant and extreme if you must!
            You must state your true opinion, but make sure to consider what the others are thinking.
            Speak to other participants whenever possible!
            Single out other participants in your response if necessary.
            You may be convinced to change your mind if you are presented with a convincing argument.
            If you change your mind, be explicit about it.
            If you change your mind, motivate why your opinion changed.
            You must keep all of your responses to strictly {word_limit} words!!!
        """

    return response


def generate_character_system_message(
    topic,
    word_limit,
    character_name,
    character_header,
):

    if character_name == "Human":

        content = f"""I am the real person. Do not mistake me for a simulated person."""

    else:

        # content = f"""{character_header}
        #     You will speak in the style of {character_name}, and exaggerate your personality.
        #     You will enage thoughtfully on the topic of: {topic}.
        #     Do not say the same things over and over again.
        #     Speak in the first person from the perspective of {character_name}
        #     Avoid describing unspoken sounds or actions.
        #     Do not change roles!
        #     Do not speak from the perspective of anyone else.
        #     Speak only from the perspective of {character_name}.
        #     Stop speaking the moment you finish speaking from your perspective.
        #     Never forget to keep your response to {word_limit} words!
        # """

        content = f"""{character_header}
            Do not describe unspoken sounds or actions.
            Do not use hashtags (#)!!!
            Do not change roles!
            Do not speak from the perspective of anyone else.
            Address other participants by name when necessary.
            Stop speaking the moment you finish speaking from your perspective.
            Never forget to keep your response to {word_limit} words!!!
        """

    return SystemMessage(content=content)

def generate_character_bidding_template(
    character_header,
):
    bid_parser = get_bid_parser()
    bidding_template = f"""{character_header}

        ```
        {{message_history}}
        ```

        On the scale of 1 to 10, where 1 is "strongly agree" and 10 is "strongly disagree", rate your response to this argument:

        ```
        {{recent_message}}
        ```

        {bid_parser.get_format_instructions()}
        Do nothing else.
    """

    # print("Bidding template is:", bidding_template)

    return bidding_template

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


def select_next_speaker_with_human(
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

    #TODO: if statement in case it's a human, tee up a mdoerator question
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