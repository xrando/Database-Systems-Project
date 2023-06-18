import configparser
import os


class ConfigManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()

        return cls._instance

    def _load_config(self):
        config = configparser.ConfigParser()
        config_route = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config.ini'))
        try:
            config.read(config_route)
            self.config = config
        except configparser.Error as e:
            print(f"Error reading config file: {e}")
            # Handle the error or raise an exception
            raise e

    def get_config(self):
        return self.config
