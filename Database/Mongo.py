from pymongo import MongoClient


class MongoDBHandler:
    _instance = None

    @staticmethod
    def get_instance(connection_string, database_name):
        if not MongoDBHandler._instance:
            MongoDBHandler._instance = MongoDBHandler(connection_string, database_name)
        return MongoDBHandler._instance

    def __init__(self, connection_string, database_name):
        if MongoDBHandler._instance:
            raise Exception("An instance of MongoDBHandler already exists. Use get_instance() to access it.")
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]
    # def __init__(self, connection_string, database_name):
    #     self.client = MongoClient(connection_string)
    #     self.db = self.client[database_name]

    def insert_document(self, collection_name, document, index: bool = False):
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            #index key fields
            if index:
                for key in document.keys():
                    collection.create_index(key)
                    print(f"Indexing {key} field")
            print(collection.index_information())
            print('Inserted ID:', result.inserted_id)
        except Exception as e:
            print(f"[-] Error inserting document into database\n {e}")

    # def find_documents(self, collection_name, query={}, limit: int = None):
    #     # if limit is None, default to 5
    #     if limit is None:
    #         limit = 5
    #     try:
    #         collection = self.db[collection_name]
    #         return list(collection.find(query).limit(limit))
    #     except Exception as e:
    #         print(f"[-] Error retrieving documents from database\n {e}")

    def find_documents(self, collection_name, query={}, limit: int = None):
        # if limit is None, default to 5
        if limit is None:
            limit = 5
        try:
            collection = self.db[collection_name]
            pipeline = [
                {'$match': query},
                {'$limit': limit}
                # Add additional stages as needed
            ]
            return list(collection.aggregate(pipeline))
        except Exception as e:
            print(f"[-] Error retrieving documents from database\n {e}")


    # options = '$set'/'$push'
    def update_document(self, collection_name, query, update_data, option):
        try:
            collection = self.db[collection_name]
            collection.update_one(query, {option: update_data})
        except Exception as e:
            print(f"[-] Error updating document in database\n {e}")

    def delete_documents(self, collection_name, query):
        try:
            collection = self.db[collection_name]
            collection.delete_one(query)
        except Exception as e:
            print(f"[-] Error deleting document in database\n {e}")

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
