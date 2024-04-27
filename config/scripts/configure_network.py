import subprocess
import json
import re
import os

def get_arp_table(interface):
    result = subprocess.run(['arp', '-i', interface, '-a'], capture_output=True, text=True)
    print(result.stderr)
    return result.stdout

def parse_arp_output(output):
    pattern = re.compile(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([\da-fA-F:]+)")
    entries = pattern.findall(output)
    return entries

def read_json_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return []

def save_to_json(entries, filename='mac_addresses.json'):
    with open(filename, 'w') as file:
        json.dump(entries, file, indent=4)

def update_devices(filename='mac_addresses.json'):
    interface = input("Name of the interface you want to scan: ")
    print("["+interface+"]")
    arp_output = get_arp_table(interface)
    arp_entries = parse_arp_output(arp_output)
    # existing_data = read_json_file(filename)
    # updated_data = {entry['MAC_address']: entry for entry in existing_data}

    updated_data = {}
    for ip, mac in arp_entries:
        # if mac in updated_data:
        #     updated_data[mac]['last_known_IP'] = ip
        # else:
            updated_data[mac] = {"MAC_address": mac, "last_known_IP": ip, "channel_id": None}

    save_to_json(list(updated_data.values()), filename)
    print("\nDevices have been updated.")

def assign_channel_ids(filename='mac_addresses.json'):
    data = read_json_file(filename)
    if not data:
        print("No devices found. Please update devices first.")
        return

    channel_count = int(input("Enter the number of channels to use: "))
    
    for i in range(channel_count):
        print("\nAvailable MAC Addresses:")
        for index, entry in enumerate(data):
            print(f"{index + 1}. MAC: {entry['MAC_address']}\t\tLast IP: {entry['last_known_IP']}\t\tCurrent Channel: {entry['channel_id']}")

        try:
            mac_index = int(input(f"Select the MAC address number to assign to channel {i + 1}: ")) - 1
            data[mac_index]['channel_id'] = i + 1
            print(f"Assigned {data[mac_index]['MAC_address']} to channel {i + 1}.")
        except (ValueError, IndexError):
            print("Invalid input. Please try again.")
            return

    save_to_json(data, filename)
    print("Channel IDs assigned successfully.")

def pulse_test(filename='mac_addresses.json'):
    data = read_json_file(filename)
    for entry in sorted(data, key=lambda x: x['channel_id']):
        if entry['channel_id']:
            print(f"Emitting network event for MAC: {entry['MAC_address']} on Channel ID: {entry['channel_id']}")

def menu():
    filename = 'mac_addresses.json'
    while True:
        print("\nMenu:\n")
        print("1. Update Devices")
        print("2. Assign Channel IDs")
        print("3. Pulse Test")
        print("4. Exit")
        choice = input("\nEnter your choice: ")

        if choice == '1':
            update_devices(filename)
        elif choice == '2':
            assign_channel_ids(filename)
        elif choice == '3':
            pulse_test(filename)
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please choose again.")

def main():
    menu()

if __name__ == "__main__":
    main()
