from typing import Callable, List
import random
import tenacity
import os
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# def specify_topic_from_prompt(
#     game_description,
#     word_limit,
#     character_names,
# ):
    
#     # content = f"""{game_description}
            
#     #     You are an evil debate moderator.
#     #     Help us make the debate topic more specific. 
#     #     Do not shy away from controversy. We like to shock and polarize people.
#     #     Keep it brief and simple.
#     #     Please reply with the specified topic in {word_limit} words or less. 
#     #     Name the participants in the debate: {*character_names,}.
#     #     Conclude by asking for an opening statement.
#     # """

#     content = f"""{game_description}
            
#         You are an evil debate moderator.
#         You must make the debate topic more specific. 
#         Do not shy away from controversy. We like to shock and polarize people.
#         If the topic of debate is binary you must not generalize it, encourage participants to take sides!
#         Keep your reply to a single sentence.
#         Your reply should always be able to be spoken out loud.
#         Avoid colons in your reply.
#         Please reply with the specified topic in {str(3 * int(word_limit))} words or less. 
#     """

#     topic_specifier_prompt = [
#         SystemMessage(content="You can make a task more specific."),
#         HumanMessage(content=content),
#     ]

#     specified_topic = llm(topic_specifier_prompt).content

#     return specified_topic

# def specify_participants(
#     specific_game_description,
#     word_limit,
#     character_names,
# ):
    
#     content = f"""You are given this specific description: {specific_game_description}
#         You are an evil debate moderator which must now introduce the participants in context.
#         Name the participants in the debate: {*character_names[1:],}.
#         Conclude by asking for an opening statement.
#         Keep the description of each participant tp a maximum of {word_limit} words!
#         Keep the opening statement to a maximum of {str(int(0.5 * int(word_limit)))} words!
#         Always begin the output by saying, "Now, the participants in this debate are:"
#     """

#     topic_specifier_prompt = [
#         SystemMessage(content="You can describe participants in context."),
#         HumanMessage(content=content),
#     ]

#     specified_topic = llm(topic_specifier_prompt).content

#     return specified_topic

# def generate_character_description(
#     character_name,
#     character_short_description,
#     game_description,
#     player_descriptor_system_message,
#     word_limit,
# ):

#     if character_name == "Human":

#         character_description = f"""
#             The real person, not a simulated person.
#         """
    
#     else:

#         message_content = f"""{game_description}
#             You are {character_name}, speak in {word_limit} words or less! 
#             Speak directly to {character_name}.
#             Speak only from your own perspective!
#             Your behavioral description is: {character_short_description}.
#             Be poignant, aggressive, and use swear words if you need to get a point across!
#             Keep everything you say to a strict maximum of {word_limit} words.
#             Do not add anything else.
#         """

#         character_specifier_prompt = [
#             player_descriptor_system_message,
#             HumanMessage(content=message_content),
#         ]

#         # print('character_specifier_prompt', character_specifier_prompt)

#         # character_description = ChatOpenAI(
#         #     openai_api_key=OPENAI_API_KEY,
#         #     temperature=1.0,
#         # )(
#         #     character_specifier_prompt
#         # ).content

#         character_description = llm(
#             character_specifier_prompt
#         ).content

#     return character_description


def generate_character_header(
    interaction_mode: str,
    interaction_description: str,
    interaction_addendum: List[str],
    # topic,
    character_name: str,
    character_description: str,
    word_limit: int,
):
    
    interaction_addendum_str = "\n".join(interaction_addendum)

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
    if interaction_mode == "confession" and character_name not in ["Human", "Clone"]:

        response = f"""
            This is your character description, in angle brackets: << {character_description} >>
            You have asked the human the following introspective question, in angle brackets: << {interaction_description} >>
            True to your character description, you must respond to the human's answer to the introspective question in the following way, in angle brackets:
            << {interaction_addendum_str} >>
            You may take the responses of other conversation participants into account when responding to the human.
            The human's answer in the conversation history will be of the format, in angle brackets: << Human: HUMAN_ANSWER >>.
            Always reply directly to the human!
            Build upon the specific content contained in the human's answer, be specific and offer an insightful analysis.
            You must keep all of your responses to strictly {word_limit} words!!!
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
        
        response = f"""This is a description of your current interaction mode, in angle brackets: << {interaction_description} >>
            This is your character description, in angle brackets: << {character_description} >>
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
    return system_message


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
            Do not use hashtags (#) or angle brackets (<<, >>)!!!
            Do not change roles!
            Do not speak from the perspective of anyone else.
            Address other participants by name when necessary.
            Stop speaking the moment you finish speaking from your perspective.
            Never forget to keep your response to {word_limit} words!!!
        """

    return content

