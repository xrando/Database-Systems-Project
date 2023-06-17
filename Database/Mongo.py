from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Create a new database
db = client['movie_db']

# Create collections
reviews = db['reviews']
watchlist = db['watchlist']
user_follows = db['user_follows']
#not sure if needed
watchlist_arr = db['watchlist_arr']
alternative_titles = db['alternative_titles']


# Insert a sample document into the collection
result = reviews.insert_one({
    'movie_id': 10,
    'ratings_arr': [4, 5, 3],
    'comments_arr': ['Great movie!', 'Loved the acting', 'Could have been better'],
})
print('Inserted ID:', result.inserted_id)

watch = watchlist.insert_one({
    'user_id': 1,
    'watchlist_arr': [1, 2, 3],
})
print('Inserted ID:', watch.inserted_id)

following = user_follows.insert_one({
    'user_id': 1,
    'following_arr': [1, 2, 3]
})
print('Inserted ID:', following.inserted_id)


cursor = reviews.find({'movie_id': 10})
for document in cursor:
     print(document)
cursor = watchlist.find({'user_id': 1})
for document in cursor:
    print(document)
cursor = user_follows.find({'user_id': 1})
for document in cursor:
    print(document)
# # Find all documents in the reviews collection
# cursor = reviews.find({})
#
# # Iterate over the documents
# for document in cursor:
#     print(document)
#
#
# # Find documents with the specific title
# query = {'movie_id': 10}
# cursor = reviews.find(query)
#
# # Iterate over the matching documents
# for document in cursor:
#     print(document)