from flask import render_template, request
from flask_login import current_user

import Database.DBMS_Movie as DBMS_Movie
import Database.Mongo as Mongo
from Config.ConfigManager import ConfigManager
from . import routes

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()

handler = Mongo.MongoDBHandler('mongodb://localhost:27017/', 'movie_db')


@routes.route('/home/page/<int:page>', methods=['GET'])
@routes.route('/home', defaults={'page': 1}, methods=['GET'])
def home(page: int) -> str:
    limit = int(config.get("MOVIE", "LIMIT"))
    pages = DBMS_Movie.get_pages(pages=page, limit=limit)
    pages_left = pages["pages_left"]
    total_pages = pages["total_pages"]

    # TODO: Convert to error page
    if page < 1:
        raise Exception('Page not found')
    elif page > total_pages:
        raise Exception('Page not found')

    carousel = DBMS_Movie.carousel()
    movie_list = DBMS_Movie.Movie_list(page=page, limit=limit)
    genres = DBMS_Movie.get_all_genres()
    kwargs = {}

    return render_template(
        'index.html',
        endpoint='routes.home',
        movie_list=movie_list,
        total_pages=total_pages,
        pages_left=pages_left,
        carousel=carousel,
        page=page,
        genre_list=genres,
        kwargs=kwargs
    )


@routes.route('/movie/<string:movie_name>', methods=['GET', 'POST'])
def movie_page(movie_name: str = None) -> str:
    """
    Get all movie details and render movie page
    :param movie_name: Movie name
    :return: Render movie page
    """
    # Remove (year) from movie name
    movie_name = movie_name.split('(')[0]
    movie = DBMS_Movie.get_movie_by_title(movie_name)

    movie_details = movie['movie']
    movie_genres = movie['genres']
    movie_director = movie['director']
    movie_actors = movie['actors']
    movie_link = movie['tmdb_link']

    # get movie reviews
    movieID = DBMS_Movie.get_movieID(movie_name)
    # json object containing all reviews for a movie
    data = handler.find_documents('reviews', {'movie_id': movieID})
    # print(data[0]['movie_id'])
    # print(data[0]['ratings'])
    # print(data[0]['comments'])
    reviews = []
    for rating, comment in zip(data[0]['ratings'], data[0]['comments']) if data != [] else []:
        reviews.append((rating, comment))

    # reviews = [(5, 'This is a test review'), (4, 'This is another test review')]

    inWatchList = False
    # Error handling just cuz
    if current_user.is_authenticated:
        # Check if movie in watchlist
        userWatchList = handler.find_documents('watchlist', {'user_id': current_user.id})
        userWatchListId = []
        if userWatchList:
            userWatchList = userWatchList[0]['watchlist_arr']
            for movie in userWatchList:
                userWatchListId.append(movie)
        else:
            handler.insert_document('watchlist', {'user_id': current_user.id, 'watchlist_arr': []})

        if movieID in userWatchListId:
            inWatchList = True
        else:
            inWatchList = False

        # Add to watchlist
        if request.method == 'POST':
            if inWatchList:
                handler.update_document('watchlist', {'user_id': current_user.id}, {'watchlist_arr': movieID},
                                        '$pull')
                inWatchList = False
            else:
                handler.update_document('watchlist', {'user_id': current_user.id}, {'watchlist_arr': movieID},
                                        '$push')
                inWatchList = True
        else:
            pass

    return render_template(
        'Movie/Movie_details.html',
        movie_name=movie_name,
        movie=movie_details,
        genres=movie_genres,
        director=movie_director,
        actors=movie_actors,
        link=movie_link,
        reviews=reviews,
        inWatchList=inWatchList
    )
