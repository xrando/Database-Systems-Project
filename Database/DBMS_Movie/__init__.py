####################################################################################################
# These are the imports for the DBMS_Movie package and the initialization of the package.          #
####################################################################################################
import os

from Config.ConfigManager import ConfigManager
import logging


# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

# Initialize the logger
file = config.get('FLASK', 'LOG_FILE') or 'log.txt'
log_dir = os.path.dirname(file)

# Create the folder and file if they don't exist
os.makedirs(log_dir, exist_ok=True)
open(file, 'a').close()

# Set the logging level to DEBUG by default
logging.basicConfig(filename=file, level=logging.DEBUG)


if config.get('TMDB', 'API_KEY') == "":
    logging.error("Please enter your TMDB API key in the config.ini file", exc_info=True)
    raise ValueError("Please enter your TMDB API key in the config.ini file")

from .Movie import *
from .Actor import *
from .Director import *
from .Search import *
from .Admin import *
