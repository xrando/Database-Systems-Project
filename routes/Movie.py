from flask import render_template, request
from flask_login import current_user

import Database.DBMS_Movie as DBMS_Movie
import Database.Mongo as Mongo
from Config.ConfigManager import ConfigManager
from . import routes

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()


handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


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


@routes.route('/movie/<string:movie_name>', methods=['GET'])
def movie_page(movie_name: str = None) -> str:
    """
    Get all movie details and render movie page
    :param movie_name: Movie name
    :return: Render movie page
    """
    # Remove (year) from movie name
    movie_name = movie_name.split('(')[0]
    movie = DBMS_Movie.movie_page(movie_name)

    movie_details = movie['movie']
    movie_genres = movie['genres']
    movie_director = movie['director']
    movie_link = movie['tmdb_link']
    movie_actors = movie['actors']
    # Get profile image from MongoDB
    actors = []
    for actor in movie_actors:
        # print(actor)
        actor_profile = DBMS_Movie.get_actor_info(actor_tmdb_id=actor[1])
        if actor_profile is not None:
            profile_path = config.get("MOVIE", "TMDB_IMAGE_URL") + actor_profile['profile_path'] if actor_profile['profile_path'] is not None else None
            actors.append([actor[0], actor[1], actor[2], profile_path])

    movie_tmdb_rating = round(movie['rating'][0] * 10) if movie['rating'] else 0

    # Delete left side of link
    movie_tmdb_id = movie_link.split(config.get("MOVIE", "TMDB_MOVIE_URL"))[1]

    movie_providers = DBMS_Movie.movie_providers(movie_tmdb_id)

    providers = []
    if movie_providers is not None:
        for key, value in movie_providers.items():
            # If key is not a link
            if key != 'link':
                for provider in value:
                    print(provider)
                    # save as [[logo_path, provider_name, display_priority], ...]
                    providers.append([
                        config.get("MOVIE", "TMDB_IMAGE_URL") + provider['logo_path'],
                                      provider['provider_name'],
                                      provider['display_priority']
                    ])

    # sort providers based on 'display_priority', Casting display_priority to int and removing duplicates
        providers = sorted(providers, key=lambda x: int(x[2]))
        providers = [providers[i] for i in range(len(providers)) if i == 0 or providers[i] != providers[i-1]]

    else:
        providers = None

    # get movie reviews
    movieID = DBMS_Movie.get_movieID(movie_name)
    # json object containing all reviews for a movie
    data = handler.find_documents(config.get('MONGODB', 'REVIEW_COLLECTION'), {'movie_id': movieID})
    # print(data[0]['movie_id'])
    # print(data[0]['ratings'])
    # print(data[0]['comments'])
    reviews = []
    rating = 0
    for rating, comment in zip(data[0]['ratings'], data[0]['comments']) if data != [] else []:
        reviews.append((rating, comment))

    # calculate average rating
    numRating = len(data[0]['ratings']) if data != [] else 0
    rating = sum(int(rating) for rating in data[0]['ratings']) / numRating if data != [] else 0
    rating = round(rating / 5 * 100)

    inWatchList = False
    # Error handling just cuz
    if current_user.is_authenticated:
        # Check if movie in watchlist
        userWatchList = handler.find_documents(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id})
        userWatchListId = []
        if userWatchList:
            userWatchList = userWatchList[0]['watchlist_arr']
            for movie in userWatchList:
                userWatchListId.append(movie)
        else:
            handler.insert_document(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id, 'watchlist_arr': []})

        inWatchList = movieID in userWatchListId
        # if movieID in userWatchListId:
        #     inWatchList = True
        # else:
        #     inWatchList = False

        # Add to watchlist
        if request.method == 'POST':
            if inWatchList:
                handler.update_document(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id}, {'watchlist_arr': movieID},
                                        '$pull')
                inWatchList = False
            else:
                handler.update_document(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id}, {'watchlist_arr': movieID},
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
        actors=actors,
        providers=providers,
        link=movie_link,
        rating=rating,
        tmdb_rating=movie_tmdb_rating,
        reviews=reviews,
        inWatchList=inWatchList
    )
