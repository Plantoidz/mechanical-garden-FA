import requests
import time
import concurrent.futures

def test_api_latency(url):
    start_time = time.time()
    response = requests.get(url)
    end_time = time.time()
    latency = end_time - start_time
    return f"{url} Latency: {latency:.3f} seconds"

urls = [
    "https://api.elevenlabs.io/v2/text-to-speech",
    "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
]

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(test_api_latency, url) for url in urls]
    for future in concurrent.futures.as_completed(futures):
        print(future.result())
