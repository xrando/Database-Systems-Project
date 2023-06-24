from bson import ObjectId
from flask import render_template, request
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
handler = Mongo.MongoDBHandler(config.get('MONGODB', 'CONNECTION_STRING'), config.get('MONGODB', 'DATABASE'))


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
            print(subject, comment, userid)
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
        postID = request.form['postid']
        userid = request.form['userid']
        print(userid)
        user = dbUser.get_user_by_id(int(userid))
        print(user)
        # print(reply)
        # print(postID)
        # if post exists, save reply to mongodb
        if handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)}):
            handler.update_document(config.get('MONGODB', 'FORUM_COLLECTION'), {'_id': ObjectId(postID)}, {
                'replies': (user[0], user[3], reply),
            }, '$push')
        else:
            print("not found")

    # grab all posts from mongodb and respective user for display, limit = 0 returns all results
    # get user following
    userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id}, 0)
    if userFollows:
        userFollows = userFollows[0]['following_arr']
        for user in userFollows:
            print('following: ' + str(user))
            # get all posts for each following, limit = 0 returns all results
            userFollowingPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'userid': user}, 0)
            if userFollowingPosts:
                # get username
                name = dbUser.get_user_by_id(user)[3]
                for post in userFollowingPosts:
                    posts.append((name, post))
    print(posts)
    return render_template('forum.html', posts=posts)
