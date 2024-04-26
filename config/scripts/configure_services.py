import json
import os

class ServiceConfigurator:
    def __init__(self, source_file, destination_file):
        self.source_file = source_file
        self.destination_file = destination_file
        self.services = self.load_services()

    def load_services(self):
        with open(self.source_file, 'r') as file:
            return json.load(file)

    def display_menu(self, service_type):
        service_list = self.services[service_type]
        print(f"\nSelect {service_type.replace('_', ' ').title()}:")
        for i, service in enumerate(service_list, start=1):
            print(f"{i}. {service['name']}")

    def select_service(self, service_type):
        index = int(input("\nEnter the number for your choice: ")) - 1
        service_list = self.services[service_type]
        if 0 <= index < len(service_list):
            return service_list[index]
        else:
            print("Invalid choice!")
            return self.select_service(service_type)

    def configure_service(self):
        self.display_menu('language_models')
        selected_language_model = self.select_service('language_models')

        self.display_menu('speech_recognition_models')
        selected_speech_recognition_model = self.select_service('speech_recognition_models')

        self.display_menu('speech_synthesis_models')
        selected_speech_synthesis_model = self.select_service('speech_synthesis_models')

        config = {
            "language_model": selected_language_model['llm_config'],
            "speech_recognition_model": selected_speech_recognition_model['speech_recognition_config'],
            "speech_synthesis_model": selected_speech_synthesis_model['speech_synthesis_config']
        }

        with open(self.destination_file, 'w') as file:
            json.dump(config, file, indent=4)

        print(f"\nConfiguration saved to {self.destination_file}.")

def main():
    source_path = os.getcwd() + '/config/files/services.json'
    destination_path = os.getcwd() + '/config/files/working/current_services.json'
    configurator = ServiceConfigurator(source_path, destination_path)
    configurator.configure_service()

if __name__ == "__main__":
    main()
