from flask import render_template
from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()


@routes.route('/director/<string:director_name>', methods=['GET'])
@routes.route('/director/<int:tmdb_id>', methods=['GET'])
def director_page(director_name: str = None, tmdb_id: int = None) -> str:
    """
    Get all director details and render director page. Either director_name or tmdb_id must be provided

    :param director_name: Director's name
    :param tmdb_id: tmdb id of director
    :return: Render director page
    """
    if not director_name and not tmdb_id:
        raise Exception('Director name or TMDB ID must be provided')

    director_details = DBMS_Movie.Director(
        director_name=director_name if director_name else None,
        director_tmdb_id=tmdb_id if tmdb_id else None,
    )

    if not director_details:
        raise Exception('Director not found')

    movie_list = director_details['movies']

    director_details = director_details['director']

    director_name = director_details['name']
    director_aka = director_details['also_known_as'] or None
    director_bio = director_details['biography'] or None
    director_birthday = director_details['birthday'] or None
    director_deathday = director_details['deathday'] or None
    director_tmdb_page = config.get('MOVIE', 'TMDB_PERSON_URL') + str(director_details['id'])
    director_profile_path = config.get('MOVIE', 'TMDB_IMAGE_URL') + director_details['profile_path'] if \
        director_details['profile_path'] else None

    return render_template(
        'Director/Director.html',
        movie_list=movie_list,
        director_name=director_name,
        director_aka=director_aka,
        director_bio=director_bio,
        director_birthday=director_birthday,
        director_deathday=director_deathday,
        director_profile_path=director_profile_path,
        director_tmdb_page=director_tmdb_page
    )
