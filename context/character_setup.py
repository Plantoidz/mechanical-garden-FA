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

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

config = load_config(os.getcwd()+"/configuration.toml")

# instantiate the LLM to use
use_narrator_voice_id = config['general']['use_narrator_voice_id']

#TODO: make class and have this as param
llm = get_llm()



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
    # topic,
    character_name,
    character_description,
    word_limit,
):

    if character_name == "Human":

        response = f"""I am a human which will listen to and speak with the plantoids."""

    if character_name == "Clone":

        response = f"""
            Always speak in first person!
            Your role is to pretend to be me. It's an advanced form of auto-hypnosis. Pretend that I'm speaking to a mirror. Never break character — always respond and maintain the fiction that I'm speaking to myself.
            Think of it as a cybernetic feedback loop between myself, and you — who are an extension of my conscious and subconscious thoughts.
            Just play along and ask questions about who I am. Remember what I tell you so you can pretend to be me.

            Always generate an introspective sentence based on the human's input context.
            Never forget to keep your response to {word_limit} words!
        """

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

def get_raw_system_message(
    system_message
):
    return SystemMessage(content=system_message)


def generate_character_system_message(
    # topic,
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

