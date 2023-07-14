import logging

from bson import ObjectId
from flask import render_template, request, abort
from flask_login import current_user
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


@routes.route('/comment', methods=['POST'])
@routes.route('/post', methods=['POST', 'GET'])
def post():
    # init
    posts = []
    # if new post, save to mongodb
    if request.path == '/post':
        # if post, save post to mongodb
        if request.method == 'POST':
            # get post data
            subject = request.form['subject']
            comment = request.form['comment']
            userid = request.form['userid']
            #return error page if no results
            if not subject and not comment:
                abort(404)
                logging.error("No subject and comment provided")
            # save to mongodb
            handler.insert_document(config.get('MONGODB', 'FORUM_COLLECTION'), {
                'subject': subject,
                'comment': comment,
                'userid': int(userid),
                'replies': [],
            })
    else:
        # if new reply, save to mongodb
        # get reply data
        reply = request.form['reply']
        #return error page if no results
        if not reply:
            abort(404)
            logging.error("No reply provided")
        postID = request.form['postid']
        userid = request.form['userid']
        user = dbUser.get_user_by_id(int(userid))
        # if post exists, save reply to mongodb
        if handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)}):
            handler.update_document(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)}, {
                'replies': (user[0], user[3], reply),
            }, '$push')
        else:
            logging.error('forum not found')

    # grab all posts from mongodb and respective user for display, limit = 0 returns all results
    # get user following
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id}, 0)
    if userFollows:
        userFollows = userFollows[0]['following_arr']
        for user in userFollows:
            # get all posts for each following, limit = 0 returns all results
            userFollowingPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'userid': user}, 0)
            if userFollowingPosts:
                # get username
                name = dbUser.get_user_by_id(user)[3]
                for post in userFollowingPosts:
                    posts.append((name, post))
    #get user posts
    userPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'userid': current_user.id}, 0)
    #append user posts
    if userPosts:
        for post in userPosts:
            posts.append((current_user.name, post))
    return render_template('forum.html', posts=posts)
