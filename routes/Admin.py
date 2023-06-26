import datetime

from bson import ObjectId
from flask import render_template, request, redirect, url_for
from flask_login import current_user

from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
from Database import Mongo
import Database.User as DBUser

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()
handler = Mongo.MongoDBHandler.get_instance(
    config.get('MONGODB', 'CONNECTION_STRING'),
    config.get('MONGODB', 'DATABASE')
)


#admin landing page
@routes.route('/admin', methods=['GET'])
def admin():
    #grab all updated posts
    allPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {})
    #grab all movie requests
    allRequests = handler.find_documents(config.get('MONGODB', 'REQUEST_COLLECTION'), {})
    #print(allPosts)
    return render_template('admin.html', posts = allPosts, requests = allRequests)

#add new movie to database
#test data, title=Main Tulsi Tere Aangan Ki, tmdb_id=172687
@routes.route('/addMovie', methods=['POST'])
def addMovie():
    movie_name = request.form['movie_name']
    tmdb_id = request.form['tmdb_id']
    print(movie_name, tmdb_id)
    DBMS_Movie.new_movie(movie_name, tmdb_id)
    return redirect(url_for('routes.admin'))


# delete movie from database
@routes.route('/deleteMovie', methods=['POST'])
def deleteMovie():
    if request.method == 'POST':
        movie_id = request.form['movie_id']
        if movie_id:
            # delete from mongodb
            DBMS_Movie.deleteMovie(movie_id)
        else:
            print("No movie_id")
    return redirect(url_for('routes.admin'))
    # print(movie_id)
    # if movie_id:
    #     DBMS_Movie.deleteMovie(movie_id)
    # return redirect(url_for('routes.admin'))


# edit movie in database
@routes.route('/editMovie/<string:movie_id>', methods=['GET'])
def editMovie(movie_id: str = None):
    if request.method == 'POST':
        movie_name = request.form['movie_name']
        release_date = request.form['release_date']
        synopsis = request.form['synopsis']
        movie_id = request.form['movie_id']
        print(movie_name, release_date, synopsis, movie_id)
        DBMS_Movie.updateMovie(movie_name, release_date, synopsis, movie_id)
        return redirect(url_for('routes.admin'))
    else:
        print(movie_id)
        if movie_id:
            # get movie data
            movie = DBMS_Movie.get_movie_by_id(movie_id)
            print(movie)
            return render_template('movieEdit.html', movie=movie)


# update movie in database
@routes.route('/updateMovie', methods=['POST'])
def updateMovie():
    movie_name = request.form['title']
    release_date = request.form['date']
    synopsis = request.form['synopsis']
    movie_id = request.form['movie_id']
    print(movie_name, release_date, synopsis, movie_id)
    # validate user input
    if movie_name and release_date and synopsis and movie_id:
        DBMS_Movie.updateMovie(movie_name, release_date, synopsis, movie_id)
    return redirect(url_for('routes.admin'))


# delete post from mongodb
@routes.route('/deletePost/<string:postID>', methods=['GET'])
def deletePost(postID: str = None):
    print(postID)
    # delete from mongodb
    handler.delete_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)})
    if current_user.username == 'admin':
        return redirect(url_for('routes.admin'))
    else:
        return redirect(url_for('routes.post'))


# edit post in mongodb
@routes.route('/editPost', methods=['POST'])
@routes.route('/editPost/<string:postID>', methods=['GET'])
def editPost(postID: str = None):
    if request.method == 'POST':
        subject = request.form['subject']
        comment = request.form['comment']
        postID = request.form['postid']
        print(subject, comment, postID)
        # grab post
        post = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)})
        print(post)
        if post:
            # update post
            handler.update_document(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)}, {
                'subject': subject,
                'comment': comment,
            }, '$set')
            return redirect(url_for('routes.post'))
    else:
        print(postID)
        # grab post
        post = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)})
        print(post)
        return render_template('forumEdit.html', post=post)


# search posts by subject
@routes.route('/searchPosts', methods=['POST'])
def searchPost():
    subject = request.form['search']
    print(subject)
    # grab all posts with subject
    allPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'subject': subject})
    return render_template('admin.html', posts=allPosts)


# submit movie request
@routes.route('/requestMovie', methods=['POST'])
def requestMovie():
    movieTitle = request.form['movieTitle']
    message = request.form['message']
    userID = request.form['userid']
    print(movieTitle, message, userID)
    # insert into mongodb
    handler.insert_document(config.get('MONGODB', 'REQUEST_COLLECTION'), {
        'userID': userID,
        'movieTitle': movieTitle,
        'message': message,
    })
    return redirect(url_for('routes.home'))


# delete movie request
@routes.route('/deleteRequest', methods=['POST'])
def deleteRequest():
    # print(requestID)
    if request.method == 'POST':
        requestID = request.form['requestid']
        # delete from mongodb
        handler.delete_documents(config.get('MONGODB', 'REQUEST_COLLECTION'), {'_id': ObjectId(requestID)})
    return redirect(url_for('routes.admin'))


@routes.route('/update/movie/', methods=['POST'])
def update_movie_info():
    """
    Movie Metadata Update
    :return: redirect to admin page
    """
    if request.method == 'POST':
        title = request.form['title'] or None
        DBMS_Movie.update_movie_info(title=title)
    return redirect(url_for('routes.admin'))
