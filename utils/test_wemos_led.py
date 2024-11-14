import socket
import time

# Replace with the IP address of your ESP8266
ESP_IP = '192.168.1.145'
ESP_PORT = 1666
LOCAL_PORT = 1667  # Local port to listen on

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)  # Set a short timeout for receiving data
sock.bind(("", LOCAL_PORT))

def send_command(command):
    """
    Send a command to the ESP8266 via UDP and wait for a response.
    """
    try:
        print(f"Sending command: {command}")
        sock.sendto(command.encode(), (ESP_IP, ESP_PORT))
        print("Command sent successfully.")
        
        # Wait to receive a response, retrying until data is received or timeout occurs
        start_time = time.time()
        data = None

        while not data and time.time() - start_time < 5:  # Retry for up to 5 seconds
            try:
                data, addr = sock.recvfrom(1024)
                if data:
                    print(f"Received response from {addr}: {data.decode()}")
            except socket.timeout:
                # If the timeout occurs but within the 5-second window, continue
                continue
        
        if not data:
            print("No response received (timeout).")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    while True:
        print("\nChoose a command to send to the ESP8266:")
        print("1: <asleep>")
        print("2: <awake>")
        print("3: <speaking>")
        print("4: <thinking>")
        print("5: <listening>")
        print("6: Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            send_command('<asleep>')
        elif choice == '2':
            send_command('<awake>')
        elif choice == '3':
            send_command('<speaking>')
        elif choice == '4':
            send_command('<thinking>')
        elif choice == '5':
            send_command('<listening>')
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please choose a valid option.")

    # Close the socket
    sock.close()

if __name__ == "__main__":
    main()
