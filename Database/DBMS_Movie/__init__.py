from Config.ConfigManager import ConfigManager

# Initialize the config manager
config_manager = ConfigManager()

# Get the configuration
config = config_manager.get_config()


if config.get('TMDB', 'API_KEY') == "":
    raise ValueError("Please enter your TMDB API key in the config.ini file")

from .Movie import Movie_list, \
    movie_page, \
    get_pages, \
    carousel, \
    Genre, \
    get_genre_pages, \
    get_all_genres, \
    get_movie_by_id, \
    new_movie, \
    movie_providers

from .Actor import Actor
from .Director import Director
from .Search import search_movies, search_directors, search_actors, get_movieID
from .Admin import deleteMovie, updateMovie, update_movie_info
