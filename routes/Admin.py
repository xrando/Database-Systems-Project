from bson import ObjectId
from flask import render_template, request, redirect, url_for
from . import routes
import Database.DBMS_Movie as DBMS_Movie
from Config.ConfigManager import ConfigManager
from Database import Mongo
import Database.User as DBUser

DBMS_Movie = DBMS_Movie
config_manager = ConfigManager()
config = config_manager.get_config()
handler = Mongo.MongoDBHandler(config.get('MONGODB', 'CONNECTION_STRING'), config.get('MONGODB', 'DATABASE'))


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

#delete movie from database
@routes.route('/deleteMovie/<string:movie_id>', methods=['GET'])
def deleteMovie(movie_id: str = None):
    print(movie_id)
    #dependancy issues when deleting
    if movie_id:
        DBMS_Movie.deleteMovie(movie_id)
    return redirect(url_for('routes.admin'))

#delete post from mongodb
@routes.route('/deletePost/<string:postID>', methods=['GET'])
def deletePost(postID: str = None):
    print(postID)
    #delete from mongodb
    handler.delete_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)})
    return redirect(url_for('routes.admin'))


#search posts by subject
@routes.route('/searchPosts', methods=['POST'])
def searchPost():
    subject = request.form['search']
    print(subject)
    #grab all posts with subject
    allPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'subject': subject})
    return render_template('admin.html', posts = allPosts)

#submit movie request
@routes.route('/requestMovie', methods=['POST'])
def requestMovie():
    movieTitle = request.form['movieTitle']
    message = request.form['message']
    userID = request.form['userid']
    print(movieTitle, message, userID)
    #insert into mongodb
    handler.insert_document(config.get('MONGODB', 'REQUEST_COLLECTION'), {
        'userID': userID,
        'movieTitle': movieTitle,
        'message': message,
    })
    return redirect(url_for('routes.home'))


#delete movie request
@routes.route('/deleteRequest/<string:requestID>', methods=['GET'])
def deleteRequest(requestID: str = None):
    print(requestID)
    #delete from mongodb
    handler.delete_documents(config.get('MONGODB', 'REQUEST_COLLECTION'), {'_id': ObjectId(requestID)})
    return redirect(url_for('routes.admin'))