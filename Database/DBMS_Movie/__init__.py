####################################################################################################
# These are the imports for the DBMS_Movie package and the initialization of the package.          #
####################################################################################################

from Config.ConfigManager import ConfigManager
import logging


# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()

# Initialize the logger
logging.basicConfig(filename=config.get('FLASK', 'LOG_FILE'), level=logging.DEBUG)


if config.get('TMDB', 'API_KEY') == "":
    logging.error("Please enter your TMDB API key in the config.ini file", exc_info=True)
    raise ValueError("Please enter your TMDB API key in the config.ini file")

from .Movie import *
from .Actor import *
from .Director import *
from .Search import *
from .Admin import *
