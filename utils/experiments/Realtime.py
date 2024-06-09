from RealtimeTTS import TextToAudioStream, SystemEngine, CoquiEngine, AzureEngine, ElevenlabsEngine
from litellm import completion


def litellm(msg):
    
    response = completion(
    model="ollama/llama3", 
    messages=msg, 
    api_base="http://localhost:11434",
    stream=True
    )
    # return(response['choices'][0]['message']['content'])
    return response

def litestream(msg):
    
    r = litellm(msg)
    for chunk in r:
        if(text_chunk := chunk["choices"][0]["delta"].get("content")) is not None:
            yield text_chunk


if __name__ == '__main__':

    print("loading engine..")
    engine = CoquiEngine() 
    print("setting up the engine")
    stream = TextToAudioStream(engine)
    print("feeding the words")
    
    messages = [{ "content": "Write a three-sentence relaxing speech","role": "user"}]



        
    #  r = litellm(messages)
    r = litestream(messages);
    print("received ----->  ", r)
    stream.feed(r)
        
    print("playing")
    stream.play()
    print("done...")
    

