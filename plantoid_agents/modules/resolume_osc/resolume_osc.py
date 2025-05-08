from pythonosc.udp_client import SimpleUDPClient
import numpy as np
import time
from typing import Optional

class ResolumeOSC:
    """
    A class to handle OSC communication with Resolume for visual state management.
    """
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

    def __init__(self, ip: str = "192.168.1.159", port: int = 7000) -> None:
        """
        Initialize the ResolumeOSC client.
        
        Args:
            ip (str): Resolume's IP address
            port (int): Resolume's OSC input port
        """
        self.ip = ip
        self.port = port
        self.client: Optional[SimpleUDPClient] = None
        self.current_xfader_pos = 0.0
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the OSC client connection."""
        try:
            self.client = SimpleUDPClient(self.ip, self.port)
            print(f"ResolumeOSC client initialized for {self.ip}:{self.port}")
        except Exception as err:
            print(f"Failed to initialize ResolumeOSC client: {err}")
            self.client = None

    def set_ai_state(self, state: str, fade_duration: float = 1.0, fade_steps: int = 20) -> bool:
        """
        Set the AI state in Resolume with a smooth transition.
        
        Args:
            state (str): The AI state to set ('speaking', 'thinking', or 'listening')
            fade_duration (float): Duration of the fade transition in seconds
            fade_steps (int): Number of steps in the fade transition
            
        Returns:
            bool: True if state was set successfully, False otherwise
        """
        if not self.client:
            print("ResolumeOSC client not initialized")
            return False

        if state not in self.STATE_TO_COLUMN:
            print(f"Unknown state: {state}")
            return False
        
        column = self.STATE_TO_COLUMN[state]
        target_xfader_pos = self.STATE_TO_XFADER_POS[state]
        
        try:
            # Trigger the target column
            self.client.send_message(f"/composition/columns/{column}/connect", 1)
            print(f"Triggered column {column} for state '{state}'")
            
            # Animate crossfader from current to target position
            positions = np.linspace(self.current_xfader_pos, target_xfader_pos, fade_steps)
            delay = fade_duration / fade_steps
            
            for pos in positions:
                self.client.send_message("/composition/crossfader/position", pos)
                time.sleep(delay)
            
            self.current_xfader_pos = target_xfader_pos
            print(f"Finished crossfade to position {target_xfader_pos} for state '{state}'")
            return True
            
        except Exception as err:
            print(f"Failed to set AI state: {err}")
            return False

    def close(self) -> None:
        """Close the OSC client connection."""
        self.client = None 