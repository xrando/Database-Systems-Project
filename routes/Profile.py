import logging

import mariadb
from flask import render_template, request, redirect, url_for, abort
from flask_login import UserMixin, current_user, login_required

from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
import Database.User as DBUser
from Database import Mongo

DBMS_Movie = DBMS_Movie
dbUser = DBUser.Database()
config_manager = ConfigManager()
config = config_manager.get_config()
handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


class User(UserMixin):
    def __init__(self, id):
        user_data = dbUser.get_user_by_id(id)
        self.id = user_data[0]
        self.username = user_data[1]
        self.password = user_data[2]
        self.name = user_data[3]
        self.email = user_data[4]
        self.dob = user_data[5]


# Profile Page
@routes.route('/profile', methods=['GET', 'POST'])
@login_required
def profile(success=None):
    # Get user's username and data
    userData = User(dbUser.get_user_by_id(current_user.id)[0])
    # Update user's data
    if request.method == 'POST':
        if request.form['formtype'] == "updateprofile":
            print("Updating profile...")
            username = request.form['username']
            password = userData.password
            profilename = request.form['profilename']
            email = request.form['email']
            dob = request.form['dob']
            dbUser.update_user(current_user.id, username, password, profilename, email, dob)
            success = 'Profile Updated'
            return redirect(url_for('routes.profile', success=success))
        elif request.form['formtype'] == "deleteaccount":
            print("Deleting account...")
            try:
                dbUser.delete_user(current_user.id)
                handler.delete_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id})
                handler.delete_documents(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id})
                dbUser.manual_commit()
                return redirect(url_for('routes.login_page'))
            except (Exception, mariadb.DataError) as e:
                print(e)
                print("Rolling back...")
                dbUser.manual_rollback()
                return redirect(url_for('routes.profile'))

    # Print our user follow list
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id})
    userFollowsName = []
    if userFollows:
        for user in userFollows[0]['following_arr']:
            if dbUser.get_user_by_id(user):
                userFollowsName.append(dbUser.get_user_by_id(user))
            else:
                handler.update_document(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id},
                                        {'following_arr': user}, '$pull')
    else:
        handler.insert_document(config.get('MONGODB', 'FOLLOW_COLLECTION'),
                                {'user_id': current_user.id, 'following_arr': []})

    # Print Movie watch list
    movieWatchList = handler.find_documents(config.get('MONGODB', 'WATCHLIST_COLLECTION'), {'user_id': current_user.id})
    movieWatchListName = []
    if movieWatchList:
        movieWatchList = movieWatchList[0]['watchlist_arr']
        for movie in movieWatchList:
            movieWatchListName.append(DBMS_Movie.get_movie_by_id(movie)[1])

    print(movieWatchListName)
    return render_template(
        'profile.html',
        userData=userData,
        success=success,
        userFollows=userFollowsName,
        movieWatchListName=movieWatchListName
    )


# Other user profile page
@login_required
@routes.route('/profile/<id>', methods=['GET', 'POST'])
def other_profile(id):
    # Get user's username and data
    userData = dbUser.get_user_by_id(id)
    if not userData:
        logging.error(f'Profile id not found.')
        abort(404)  # Raise a 404 error if profile id does not exist

    # Check if user is same as current user
    if str(id) == str(current_user.id):
        return redirect(url_for('routes.profile'))

    # Check if user is followed
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id})
    if userFollows:
        if userData[0] in userFollows[0]['following_arr']:
            followed = True
        else:
            followed = False
    else:
        handler.insert_document(config.get('MONGODB', 'FOLLOW_COLLECTION'),
                                {'user_id': current_user.id, 'following_arr': []})
    # Default follow value
    followed = False

    # Print our user follow list
    userFollows = handler.find_documents('user_follows', {'user_id': userData[0]})
    userFollowsName = []
    if userFollows:
        userFollows = userFollows[0]['following_arr']
        for user in userFollows:
            userFollowsName.append(dbUser.get_user_by_id(user))

    # Print Movie watch list
    movieWatchList = handler.find_documents('watchlist', {'user_id': userData[0]})
    movieWatchListName = []
    if movieWatchList:
        for movie in movieWatchList[0]['watchlist_arr']:
            movieWatchListName.append(DBMS_Movie.get_movie_by_id(movie)[1])

    # Functions that require user to be authenticated
    if current_user.is_authenticated:
        # Check if user is followed
        userFollows = handler.find_documents('user_follows', {'user_id': current_user.id})
        if userFollows:
            if userData[0] in userFollows[0]['following_arr']:
                followed = True
            else:
                followed = False
        else:
            handler.insert_document('user_follows', {'user_id': current_user.id, 'following_arr': []})

    # Follow user
    if request.method == 'POST':
        print("Is user followed: " + str(followed))
        if not followed:
            handler.update_document(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id},
                                    {'following_arr': userData[0]},
                                    '$push')
        else:
            handler.update_document(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id},
                                    {'following_arr': userData[0]},
                                    '$pull')
        return redirect(url_for('routes.other_profile', id=id))
        # Follow user

    # Print our user follow list
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': userData[0]})
    userFollowsName = []
    if userFollows:
        userFollows = userFollows[0]['following_arr']
        for user in userFollows:
            userFollowsName.append(dbUser.get_user_by_id(user))

    return render_template(
        'profile_view.html',
        userData=userData,
        followed=followed,
        userFollows=userFollowsName,
        movieWatchListName=movieWatchListName
    )
