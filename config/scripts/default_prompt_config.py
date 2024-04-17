def default_chat_completion_config(model="gpt-3.5-turbo"):
    """
    Return a GPT model configuration dict for the chatCompletion method from passed parameters.

    Params:
    - model: a model parameter string
    """
    if model=="gpt-4":

        return {
            "model": "gpt-4",
            "temperature": 0.5,
            "max_tokens": 128,
            "logit_bias": {
                198: -100  # prevent newline
            }
        }
    
    if model == "gpt-3.5-turbo":

        return {
            "model": "gpt-3.5-turbo",
            "temperature": 0.5,
            "max_tokens": 128,
            "logit_bias": {
                198: -100  # prevent newline
            }
        }
    
    else:

        # This is the default fallback config, can be anything
        return {
            "model": "gpt-3.5-turbo",
            "temperature": 0.5,
            "max_tokens": 128,
            "logit_bias": {
                198: -100  # prevent newline
            }
        }
    
def default_completion_config(model="text-davinci-003"):
    """
    Return a GPT model configuration dict for the completion method from passed parameters.

    Params:
    """

    # TODO: add others
    return {
        "engine": "text-davinci-003",
        "max_tokens": 1024,
    }