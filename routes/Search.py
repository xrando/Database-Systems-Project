from flask import render_template, request
from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
import Database.User as DBUser

DBMS_Movie = DBMS_Movie
dbUser = DBUser.Database()
config_manager = ConfigManager()
config = config_manager.get_config()


@routes.route('/search', methods=['POST'])
def search():
    #choice = request.form['choice']
    query = request.form['search']
    # if choice == 'director':
    #     # search for directors
    #     results = DBMS_Movie.search_directors(query)
    #     print(results)
    # elif choice == 'actor':
    #     # search for actors
    #     results = DBMS_Movie.search_actors(query)
    # elif choice == 'movie':
    #     # search for movie
    #     results = DBMS_Movie.search_movies(query)
    # elif choice == 'profile':
    #     # search for user profile
    #     results = dbUser.search_user(query)
    # else:
    #     # Handle invalid choice
    #     results = []
    director_results = DBMS_Movie.search_directors(query)
    actor_results = DBMS_Movie.search_actors(query)
    movie_results = DBMS_Movie.search_movies(query)
    profile_results = dbUser.search_user(query)
    return render_template('search.html', directors=director_results, actors=actor_results, movies=movie_results, profiles=profile_results)
