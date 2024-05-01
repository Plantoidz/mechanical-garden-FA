import json
import os
import subprocess
import re
import serial
import sys
# import utils.serial_utils
import serial.tools.list_ports
# from utils.serial_utils import send_to_arduino

class CharacterConfigurator:
    def __init__(self, source_path, destination_file):
        self.source_path = source_path
        self.destination_file = destination_file
        self.characters = self.load_characters()

    def load_characters_old(self):
        with open(self.source_path, 'r') as file:
            return json.load(file)['characters']
        
    def load_characters(self):
        char_classes = None
        with open(self.source_path + "/character_bank.json", 'r') as file:
            return json.load(file)

    def select_character(self, jdump):
        index = int(input("\nSelect an option:")) - 1
        if 0 <= index < len(jdump):
            return jdump[index]
        else:
            print("Invalid choice!")
            return self.select_character(jdump)

    def select_character_name(self, defaultname):
        name = input(f"Enter the name of the character (default is {defaultname}): ")
        if(not name): name = defaultname
        return name
        
    def select_channel_id(self, i):
        index = input(f"Enter the channel ID for the character (default is {i}): ")
        if(not index): index = i
        if 0 <= index < 1000:
            return index
        else:
            print("Invalid choice, must be between 0 and 1000") ## TODO increase to allow for more channels!
        return index
    

    

    def select_Wifi(self):

        # result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        # print(result.stderr)
        # print(result.stdout)

        # pattern = re.compile(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([\da-fA-F:]+)")
        # entries = pattern.findall(result.stdout)

        # for ip, mac in entries:
        #     print("MAC_address: ", mac, "last_known_IP: ", ip)

        index = str(input("Enter the IP address of the character (press enter to ignore): "))
        return index
    

    def select_Serial(self):

        ports = serial.tools.list_ports.comports()
        serial_ports = []
        for port, desc, hwid in sorted(ports):
                    print("{}: {} [{}]".format(port, desc, hwid))
                    #if("USB" in desc): serial_ports.append(port)
                    serial_ports.append(port)

        print(serial_ports)
        index = str(input("Enter the serial port of the character: "))
        return index

    def select_addr(self, io):
        if(io == "wifi"):
            r = self.select_Wifi()
            return r
        
        elif (io == "serial"):
            r = self.select_Serial()
            return r
        
        
    def select_comm_io(self):

        return str(input("Choose the I/O communication type (serial or wifi) - press <enter> for None: "))
      


    def display_menu(self, jdump):
            for i, character in enumerate(jdump, start=1):
                print(f"{i}. {character['name']}")



    def configure_characters(self):
        num_of_characters = int(input("\nHow many characters do you want to select? "))

        while num_of_characters <= 0 or num_of_characters > len(self.characters):

            print("Invalid number. Please enter a number between 1 and the total number of characters.")
            num_of_characters = int(input("How many characters do you want to select? "))

        selected_characters = []
        selected_characters_map = {}

        for i in range(num_of_characters):

            print(f"\nSelect type for character {i + 1}:\n")



            for k in range(len(self.characters)):

                print(f"{k+1}.", self.characters[k]['description'])

            stimuli = int(input(f"\nSelect a character:\n")) -1

            with open(self.source_path + "/" + self.characters[stimuli]['stimuli'], 'r') as ffile:
                    jdump = json.load(ffile)['characters']
        


                    self.display_menu(jdump)
                    choice = self.select_character(jdump)

                    name = self.select_character_name(choice['name'])
                    choice['name'] = name

                    selected_characters_map[name] = i  # Mapping name to the default channel
                    # channel_id = int(self.select_channel_id(i))

                    channel_id = self.select_channel_id(i)
                    
                    choice['default_channel'] = channel_id

                    comm_io = self.select_comm_io()
                    choice['io'] = comm_io

                    addr = self.select_addr(comm_io)
                    choice['addr'] = addr

                    selected_characters.append(choice)

       
        # for character in selected_characters:
        #     if character['name'] in selected_characters_map:
        #         character['default_channel'] = selected_characters_map[character['name']]

        config = {"characters": selected_characters}

        with open(self.destination_file, 'w') as file:
            json.dump(config, file, indent=4)

        print(f"\nConfig saved to {self.destination_file} with the {num_of_characters} selected characters only.")

def main():
    source_path = os.getcwd()+'/config/files/characters/'
    destination_path = os.getcwd()+'/config/files/working/current_characters.json'
    configurator = CharacterConfigurator(source_path, destination_path)
    configurator.configure_characters()

if __name__ == "__main__":
    main()
