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

@routes.route('/post', methods=['POST', 'GET'])
def post():
    allPostsToDisplay = []
    #if post, save post to mongodb
    if request.method == 'POST':
        #get post data
        subject = request.form['subject']
        comment = request.form['comment']
        userid = request.form['userid']
        print(subject, comment, userid)
        #save to mongodb
        handler.insert_document(config.get('MONGODB', 'FORUM_COLLECTION'), {
            'subject': subject,
            'comment': comment,
            'userid': int(userid),
        })


    #if get, grab all posts from mongodb and match with user
    if request.method == 'GET':
        #get user following
        userFollows = handler.find_documents(config.get('MONGODB', 'FOLLOW_COLLECTION'), {'user_id': current_user.id})
        if userFollows:
            userFollows = userFollows[0]['following_arr']
            for user in userFollows:
                #userFollowsName.append(dbUser.get_user_by_id(user))
                print('following: '+str(user))
                #get all posts for each following
                userFollowingPosts = handler.find_documents(config.get('MONGODB', 'FORUM_COLLECTION'), {'userid': user})
                if userFollowingPosts:
                    #append each post to allPostsToDisplay
                    for post in userFollowingPosts:
                        allPostsToDisplay.append(post)
                        print(post)




    return render_template('forum.html', posts = allPostsToDisplay)