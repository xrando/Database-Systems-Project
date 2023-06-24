from pymongo import MongoClient

class MongoDBHandler:
    def __init__(self, connection_string, database_name):
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]

    def insert_document(self, collection_name, document):
        collection = self.db[collection_name]
        result = collection.insert_one(document)
        print('Inserted ID:', result.inserted_id)

    def find_documents(self, collection_name, query={}):
        collection = self.db[collection_name]
        return list(collection.find(query))
    #options = '$set'/'$push'
    def update_document(self, collection_name, query, update_data, option):
        collection = self.db[collection_name]
        collection.update_one(query, {option: update_data})

    def delete_documents(self, collection_name, query):
        collection = self.db[collection_name]
        collection.delete_one(query)


# Example usage:
# handler = MongoDBHandler('mongodb://localhost:27017/', 'movie_db')
#
# handler.insert_document('reviews', {
#     'movie_id': 10,
#     'ratings_arr': [4, 5, 3],
#     'comments_arr': ['Great movie!', 'Loved the acting', 'Could have been better'],
# })
#
# handler.insert_document('watchlist', {
#     'user_id': 1,
#     'watchlist_arr': [1, 2, 3],
# })
#
# handler.insert_document('user_follows', {
#     'user_id': 1,
#     'following_arr': [1, 2, 3],
# })
#
#
# cursor = handler.find_documents('reviews', {'movie_id': 10})
# for document in cursor:
#     print(document)
#
# cursor = handler.find_documents('watchlist', {'user_id': 1})
# for document in cursor:
#     print(document)
#
# cursor = handler.find_documents('user_follows', {'user_id': 1})
# for document in cursor:
#     print(document)
