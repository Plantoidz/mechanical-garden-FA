async def audio_streaming():
    audio_stream = tts.generate(
        text=text_streaming(prompt),
        voice="5g2h5kYnQtKFFdPm8PpK",
        model="eleven_turbo_v2",
        stream=True
    )
    stream(audio_stream)
    
def text_streaming(str:prompt, str:role):
    response = completion(
        model=llm_config, 
        messages=[{"content": prompt, "role": role}], 
        messages=messages, 
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta
            text_chunk = delta.content
            yield text_chunk
            print(text_chunk, end='', flush=True)

# we create an agent like this; all of these attributes are optional; they need to be async

agent1 = PlantoidAgent(role="1", channel="1", personality="1", address="1", id="1")
agent2 = PlantoidAgent(role="1", channel="1", personality="1", address="1", id="1")

# we can call them like this

agent1.listen(id="1", )
agent1.speak("Welcome to the garden")

############################################################
### Listen does something like this ###
############################################################

# if "id" attribute exists, try to load messages from working/{id}_messages.json
    # else, id is generated from current timestamp

# get the prompt
transcription = DeepgramTranscription()
transcription.start_listening()
prompt = transcription.get_final_result()

# create or append to the conversation in memory:

[
    { "content": "{prompt}", "role": "user" }
]

# write to working/{id}.json

# if speakafter=True
    await audio_streaming()

# create or append to the conversation in memory:

[
    { "content": "{response}", "role": "assistant" }
]

# write to working/{id}_messages.json

############################################################
### Speak does something like this ###
############################################################

# if "id" attribute exists, try to load messages from working/{id}_messages.json
    # otherwise, id is generated from current timestamp

# if string was passed, say the thing, 

    audio_stream = tts.generate(
        text=(str),
        voice="5g2h5kYnQtKFFdPm8PpK",
        model="eleven_turbo_v2",
        stream=True
    )
    stream(audio_stream)

    # and create or append to the conversation in memory:

    [
        { "content": "{str}", "role": "assistant" }
    ]

    # write to working/{id}_messages.json

        # else, generate a completion

        async def audio_streaming():
            audio_stream = tts.generate(
                text=text_streaming(messages),
                voice="5g2h5kYnQtKFFdPm8PpK",
                model="eleven_turbo_v2",
                stream=True
            )
            stream(audio_stream)

        # and create or append to the conversation in memory:

        [
            { "content": "{response}", "role": "assistant" }
        ]

        # write to working/{id}.json

# if listenafter=True, call self.listen



MEMORY:

If an id attribute is provided, try to load the conversation history (this would be in working/{id}.json)

LATER:

agent1.condense()
agent1.summarize()


[
    { "content": "{prompt}?", "role": "user" }
    { "content": "I'm doing great, thanks for asking! How can I help you today?", "role": "assistant" },
    { "content": "I'm curious about the latest space missions. Can you tell me about any recent launches?", "role": "user" },
    { "content": "Certainly! Recently, several exciting space missions have been launched. For example, NASA launched a mission to study the sun's atmosphere, and SpaceX sent a new batch of satellites into orbit to improve global internet coverage. Would you like more detailed information on any specific mission?", "role": "assistant" },
    { "content": "Yes, please tell me more about the NASA mission to study the sun's atmosphere.", "role": "user" }
]


