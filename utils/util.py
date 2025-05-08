import toml
import requests
import os

def load_config(config_path=None):

    if config_path is None:
        config_path = os.getcwd()+"/configuration.toml"

    return toml.load(config_path)

def str_to_bool(s):
    s = s.strip().lower()
    lookup = {'true': True, 'false': False}
    return lookup.get(s, "Invalid literal for boolean")


def api_request(url, method="GET", data=None, headers=None, timeout=10):
    """
    Wrapper function for requests.get and requests.post.

    Parameters:
    - url (str): The URL to make the request to.
    - method (str): Either "GET" or "POST". Defaults to "GET".
    - data (dict): The data to send in the request. Used for POST requests. Defaults to None.
    - headers (dict): The headers to send with the request. Defaults to None.
    - timeout (int): The request timeout in seconds. Defaults to 10 seconds.

    Returns:
    - data (dict): The JSON data from the response or None if an error occurs or response is not JSON.
    """
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, data=data, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()

        # Attempt to parse the response content as JSON and return
        return response.json()

    except requests.ConnectionError:
        print("Failed to connect to the server.")
    except requests.Timeout:
        print("Request timed out.")
    except requests.RequestException as error:
        print(f"An error occurred: {error}")
    except requests.HTTPError:
        print(f"HTTP error occurred: {response.text}")
    except ValueError:  # If JSON decoding fails
        print("Failed to parse response as JSON.")
    
    return None

def read_additional_context(character_name: str, context_dir: str = "config/files/additional_context") -> str:
    """
    Reads additional context for a character from a file.
    
    Parameters:
    - character_name (str): The name of the character.
    - context_dir (str): The directory containing additional context files. Defaults to "config/files/additional_context".
    
    Returns:
    - str: The additional context as a string, or an empty string if the file doesn't exist.
    """
    additional_context = ""
    additional_context_path = os.path.join(context_dir, f"{character_name.lower()}.txt")
    
    if os.path.exists(additional_context_path):
        try:
            with open(additional_context_path, 'r') as f:
                additional_context = f.read().strip()
        except Exception as e:
            print(f"Error reading additional context file for {character_name}: {e}")
    
    return additional_context

def read_character_description(character_name: str, descriptions_dir: str = "config/files/characters/extra_descriptions") -> str:
    """
    Reads an extra character description from a file.
    
    Parameters:
    - character_name (str): The name of the character.
    - descriptions_dir (str): The directory containing character description files. 
                             Defaults to "config/files/characters/extra_descriptions".
    
    Returns:
    - str: The character description as a string, or an empty string if the file doesn't exist.
    """
    description = ""
    description_path = os.path.join(descriptions_dir, f"{character_name.lower()}.txt")
    
    if os.path.exists(description_path):
        try:
            with open(description_path, 'r') as f:
                description = f.read().strip()
        except Exception as e:
            print(f"Error reading character description file for {character_name}: {e}")
    
    return description