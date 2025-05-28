import json

class FileStorage:
    @staticmethod
    def save_to_file(data, file_name):
        """
        Save data to a file in JSON format.
        :param data: Data to be saved
        :param file_name: File name for storage
        """
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {file_name}")

    @staticmethod
    def load_from_file(file_name):
        """
        Load data from a JSON file.
        :param file_name: File name to load data from
        :return: Loaded data
        """
        try:
            with open(file_name, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"No file found: {file_name}")
            return None