from flask import render_template
from . import routes
import Database.DBMS_Movie as DBMS_Movie
import Database.User as DBUser
import configparser

DBMS_Movie = DBMS_Movie.DBMS_Movie
dbUser = DBUser.Database()
config = configparser.ConfigParser()
config.read('../Config/config.ini')


@routes.route('/actor/<string:actor_name>', methods=['GET'])
@routes.route('/actor/<int:tmdb_id>', methods=['GET'])
def actor(actor_name: str = None, tmdb_id: int = None) -> str:
    """
    Get all actor details and render actor page. Either actor_name or tmdb_id must be provided

    :param order:
    :param order_by:
    :param actor_name: Actor's name
    :param tmdb_id: Actor's TMDB ID
    :return:
    """
    if not actor_name and not tmdb_id:
        raise Exception('Actor name or TMDB ID must be provided')

    actor_details = DBMS_Movie.Actor(
        actor_name=actor_name if actor_name else None,
        actor_tmdb_id=tmdb_id if tmdb_id else None,
    )

    if not actor_details:
        # TODO: Convert to error page
        raise Exception('Actor not found')

    movie_list = actor_details['movies']

    actor_details = actor_details['actor']
    actor_name = actor_details['name']
    actor_aka = actor_details['also_known_as']
    actor_bio = actor_details['biography']
    actor_birthday = actor_details['birthday']
    actor_deathday = actor_details['deathday']
    actor_tmdb_page = config.get('MOVIE', 'TMDB_PERSON_URL') + str(actor_details['id'])
    actor_profile_path = config.get('MOVIE', 'TMDB_IMAGE_URL') + actor_details['profile_path'] if \
        actor_details['profile_path'] else None

    return render_template(
        'Actor/Actor.html',
        actor_name=actor_name,
        actor_aka=actor_aka,
        actor_bio=actor_bio,
        actor_birthday=actor_birthday,
        actor_deathday=actor_deathday,
        actor_profile_path=actor_profile_path,
        actor_tmdb_page=actor_tmdb_page,
        movie_list=movie_list
    )
