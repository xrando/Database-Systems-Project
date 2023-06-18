from flask import render_template, request
from . import routes
import Database.DBMS_Movie as DBMS_Movie
import Database.User as DBUser
import configparser

DBMS_Movie = DBMS_Movie
dbUser = DBUser.Database()
config = configparser.ConfigParser()
config.read('../Config/config.ini')


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
