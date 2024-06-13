import toml
import requests
import os

def get_working_path():
    path = os.environ.get("WORKING_PATH")
    if(not path):
        path = os.getcwd()
    return path


def load_config(config_path=None):

    if config_path is None:
        config_path = get_working_path()+"/configuration.toml"

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