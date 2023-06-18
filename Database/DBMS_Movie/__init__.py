from .ConfigManager import ConfigManager

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()


if config.get('TMDB', 'API_KEY') == "":
    raise ValueError("Please enter your TMDB API key in the config.ini file")

from .Movie import Movie_list, get_movie_by_title, get_pages, carousel
from .Actor import Actor
from .Director import Director
from .Search import search_movies, search_directors, search_actors, get_movieID
