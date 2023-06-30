from flask import render_template, request
from flask_login import current_user

import Database.DBMS_Movie as DBMS_Movie
import Database.Mongo as Mongo
from Config.ConfigManager import ConfigManager
from . import routes
import concurrent.futures

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()

handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


@routes.route('/home/page/<int:page>', methods=['GET'])
@routes.route('/home', defaults={'page': 1}, methods=['GET'])
@routes.route('/', defaults={'page': 1}, methods=['GET'])
def home(page: int) -> str:
    """
    Homepage of The project
    :param page: Page Number
    :type page: int
    :return: Render of index.html
    """

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
    recommendations = DBMS_Movie.movie_recommendation(current_user.id) if current_user.is_authenticated else None
    kwargs = {}

    return render_template(
        'index.html',
        endpoint='routes.home',
        movie_list=movie_list,
        total_pages=total_pages,
        recommendations=recommendations,
        pages_left=pages_left,
        carousel=carousel,
        page=page,
        genre_list=genres,
        kwargs=kwargs
    )


@routes.route('/movie/<string:movie_name>/cast', methods=['GET'])
@routes.route('/movie/<string:movie_name>', methods=['GET', 'POST'])
def movie_page(movie_name: str = None) -> str:
    """
    Get all movie details and render movie page
    :param movie_name: Movie name
    :return: Render movie page
    """

    # Return Variables
    movie = None
    movie_details = None
    movie_genres = None
    movie_director = None
    movie_link = None
    movie_year = None
    actors = None
    providers = None
    rating = None
    movie_tmdb_rating = None
    reviews = None
    inWatchList = None

    try:
        # Remove (year) from movie name
        if movie_name is not None:
            try:
                movie_name, movie_year = movie_name.split('(')
            except ValueError:
                movie_year = None

            movie = DBMS_Movie.movie_page(movie_name)

            if movie == {} or movie is None:
                # TODO: Convert to error page
                raise Exception('Movie not found')

            movie_details = movie.get('movie')
            movie_genres = movie.get('genres')
            movie_director = movie.get('director')
            movie_link = movie.get('tmdb_link')
            movie_actors = movie.get('actors')

            # Movie year is none, get from movie details[1]
            if movie_year is None:
                if movie_details is not None and len(movie_details) > 1:
                    movie_year = movie_details[1].split(' ')[-1]
                else:
                    movie_year = None
                if movie_year:
                    movie_year = movie_year + ')'

            # If no /cast
            if request.path == f'/movie/{movie_name}({movie_year}/cast':
                movie_actors = movie_actors
            else:
                movie_actors = movie_actors[:3]
        else:
            movie_details = None
            movie_genres = None
            movie_director = None
            movie_link = None
            movie_actors = None

        # Get profile image from MongoDB
        actors = []
        if movie_actors:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                actor_profiles = executor.map(lambda actor: DBMS_Movie.get_actor_info(actor_tmdb_id=actor[1]),
                                              movie_actors)

            for actor, actor_profile in zip(movie_actors, actor_profiles):
                if actor_profile is not None:
                    profile_path = config.get("MOVIE", "TMDB_IMAGE_URL") + actor_profile.get('profile_path',
                                                                                             '') if actor_profile.get(
                        'profile_path') is not None else None
                    actors.append([actor[0], actor[1], actor[2], profile_path])

        movie_tmdb_rating = round(movie.get('rating')[0] * 10) if movie.get('rating') else 0

        # Delete left side of link
        movie_tmdb_id = movie_link.split(config.get("MOVIE", "TMDB_MOVIE_URL"))[1]

        movie_providers = DBMS_Movie.movie_providers(movie_tmdb_id)

        providers = []
        if movie_providers is not None:
            for key, value in movie_providers.items():
                # If key is not a link
                if key != 'link':
                    for provider in value:
                        # save as [[logo_path, provider_name, display_priority], ...]
                        providers.append([
                            config.get("MOVIE", "TMDB_IMAGE_URL") + provider['logo_path'],
                            provider['provider_name'],
                            provider['display_priority']
                        ])

            # sort providers based on 'display_priority', Casting display_priority to int and removing duplicates
            providers = sorted(providers, key=lambda x: int(x[2]))
            providers = [providers[i] for i in range(len(providers)) if i == 0 or providers[i] != providers[i - 1]]

        else:
            providers = None

        # get movie reviews
        movieID = DBMS_Movie.get_movieID(movie_name)
        # json object containing all reviews for a movie
        data = handler.find_documents(config.get('MONGODB', 'REVIEW_COLLECTION'), {'movie_id': movieID})
        reviews = []
        rating = 0
        if data:
            ratings = data[0].get('ratings', [])
            comments = data[0].get('comments', [])
            reviews = list(zip(ratings, comments))
            numRating = len(ratings)
            rating = sum(int(rating) for rating in ratings) / numRating if numRating != 0 else 0
            rating = round(rating / 5 * 100)

        inWatchList = False
        # Error handling just in case
        if current_user.is_authenticated:
            # Check if movie in watchlist
            userWatchList = handler.find_documents(config.get('MONGODB', 'WATCHLIST_COLLECTION'),
                                                   {'user_id': current_user.id})
            userWatchListId = []
            if userWatchList:
                userWatchList = userWatchList[0].get('watchlist_arr', [])
                for movie in userWatchList:
                    userWatchListId.append(movie)
            else:
                handler.insert_document(config.get('MONGODB', 'WATCHLIST_COLLECTION'),
                                        {'user_id': current_user.id, 'watchlist_arr': []})

            inWatchList = movieID in userWatchListId

            # Add to watchlist
            if request.method == 'POST':
                if inWatchList:
                    handler.update_document(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id},
                                            {'watchlist_arr': movieID}, '$pull')
                    inWatchList = False
                else:
                    handler.update_document(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id},
                                            {'watchlist_arr': movieID}, '$push')
                    inWatchList = True
    except (ValueError, KeyError, TypeError) as e:
        error_message = str(e)
        print(f"Error: {error_message}")

    return render_template(
        'Movie/Movie_details.html',
        movie_name=movie_name,
        movie_year=movie_year,
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
