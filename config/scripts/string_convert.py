import os
import json

def convert_to_single_line_json(input_file_path, output_file_path):
    # Open the input file for reading
    with open(input_file_path, 'r') as file:
        # Read all lines from the file
        content = file.read()
    
    # Escape the content for JSON
    # This automatically escapes special characters like \, ", and control characters
    json_encoded_content = json.dumps(content)
    
    # json.dumps() adds additional double quotes at the beginning and end which we don't need
    # if embedding as a value in a JSON object, so remove them
    json_encoded_content = json_encoded_content[1:-1]
    
    # Replace newlines with \n within the string, preserving other escapes
    json_encoded_content = json_encoded_content.replace('\\n', '\\\\n')

    # Open the output file for writing
    with open(output_file_path, 'w') as file:
        # Write the transformed content to the output file
        file.write(json_encoded_content)

# Example usage
input_path = os.getcwd()+'/config/files/plantoid_context.txt'
output_path = os.getcwd()+'/config/files/plantoid_context_single_line.txt'
convert_to_single_line_json(input_path, output_path)
