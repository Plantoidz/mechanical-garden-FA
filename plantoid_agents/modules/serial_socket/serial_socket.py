import socket
from typing import Optional

class SerialSocket:
    """
    A class to handle socket communication with ESP devices.
    """
    def __init__(self, ip_address: str, port: int = 1666) -> None:
        """
        Initialize the SerialSocket with the target IP address and port.
        
        Args:
            ip_address (str): The IP address of the ESP device
            port (int, optional): The port number. Defaults to 1666.
        """
        self.ip_address = ip_address
        self.port = port
        self.socket: Optional[socket.socket] = None
        self._initialize_socket()

    def _initialize_socket(self) -> None:
        """Initialize the UDP socket connection."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"Socket initialized for {self.ip_address}:{self.port}")
        except Exception as err:
            print(f"Failed to initialize socket: {err}")
            self.socket = None

    def send_message(self, message: str) -> bool:
        """
        Send a message to the ESP device.
        
        Args:
            message (str): The message to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not self.socket:
            print("Socket not initialized")
            return False
            
        try:
            command = bytes(message, 'utf-8')
            self.socket.sendto(command, (self.ip_address, self.port))
            return True
        except Exception as err:
            print(f"Failed to send message to {self.ip_address}:{self.port} with error: {err}")
            return False

    def close(self) -> None:
        """Close the socket connection."""
        if self.socket:
            self.socket.close()
            self.socket = None 