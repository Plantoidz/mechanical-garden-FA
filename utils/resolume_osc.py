from pythonosc.udp_client import SimpleUDPClient
import numpy as np
import time

# Resolume setup
ip = "192.168.1.159"  # Localhost; change if Resolume is on another machine
port = 7000       # Resolume's default OSC input port
client = SimpleUDPClient(ip, port)

# Map AI states to Resolume columns (1-based indices)
STATE_TO_COLUMN = {
    "speaking": 1,
    "thinking": 2,
    "listening": 3
}

# Map AI states to crossfader positions
# Assuming left=0.0 (column 1), center=0.5 (column 2), right=1.0 (column 3)
STATE_TO_XFADER_POS = {
    "speaking": 0.0,
    "thinking": 0.5,
    "listening": 1.0
}

# Keep track of the current crossfader position
current_xfader_pos = 0.0

def set_ai_state(state, fade_duration=1.0, fade_steps=20):
    global current_xfader_pos
    if state not in STATE_TO_COLUMN:
        print(f"Unknown state: {state}")
        return
    
    column = STATE_TO_COLUMN[state]
    target_xfader_pos = STATE_TO_XFADER_POS[state]
    
    # Trigger the target column (this starts the clips in the column)
    client.send_message(f"/composition/columns/{column}/connect", 1)
    print(f"Triggered column {column} for state '{state}'")
    
    # Animate crossfader from current to target position
    positions = np.linspace(current_xfader_pos, target_xfader_pos, fade_steps)
    delay = fade_duration / fade_steps
    
    for pos in positions:
        client.send_message("/composition/crossfader/position", pos)
        time.sleep(delay)
    
    current_xfader_pos = target_xfader_pos
    print(f"Finished crossfade to position {target_xfader_pos} for state '{state}'")

# Example usage
if __name__ == "__main__":
    # Simulate changing states
    set_ai_state("speaking")
    time.sleep(3)
    
    set_ai_state("thinking")
    time.sleep(3)
    
    set_ai_state("listening")
    time.sleep(3)
    
    set_ai_state("speaking")
