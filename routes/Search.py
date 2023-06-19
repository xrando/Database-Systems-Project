from flask import render_template, request
from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()


@routes.route('/search', methods=['POST'])
def search():
    choice = request.form['choice']
    query = request.form['search']
    if choice == 'director':
        # search for directors
        results = DBMS_Movie.search_directors(query)
        print(results)
    elif choice == 'actor':
        # search for actors
        results = DBMS_Movie.search_actors(query)
    elif choice == 'movie':
        # search for movie
        results = DBMS_Movie.search_movies(query)
    else:
        # Handle invalid choice
        results = []
    return render_template('search.html', results=results, choice=choice)

#display movies via genre, ratings etc
@routes.route('/movie', methods=['GET'])
def movie():
    #grab latest movies



    #grab highly rated movies


    #grab movies by genre
    search_genres('Action')





    return render_template(
        'Movie/movies_display.html'
    )