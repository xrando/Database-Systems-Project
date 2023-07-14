import logging

from pymongo import MongoClient
from pydantic import BaseModel, ValidationError
import bleach

class MongoDBHandler:
    _instance = None

    @staticmethod
    def get_instance(connection_string, database_name):
        if not MongoDBHandler._instance:
            MongoDBHandler._instance = MongoDBHandler(connection_string, database_name)
        return MongoDBHandler._instance

    def __init__(self, connection_string, database_name):
        if MongoDBHandler._instance:
            logging.error('An instance of MongoDBHandler already exists. Use get_instance() to access it.')
            raise Exception("An instance of MongoDBHandler already exists. Use get_instance() to access it.")
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]

    def sanitize_input(self, document):
        # Sanitize input using Bleach
        sanitized_document = {}
        for key, value in document.items():
            if isinstance(value, str):
                sanitized_value = bleach.clean(value)
                sanitized_document[key] = sanitized_value
            else:
                sanitized_document[key] = value
        return sanitized_document

    def insert_document(self, collection_name, document, index: bool = False):
        try:
            # Sanitize input
            sanitized_document = self.sanitize_input(document)

            collection = self.db[collection_name]
            result = collection.insert_one(sanitized_document)

            # Index key fields
            if index:
                for key in sanitized_document.keys():
                    collection.create_index(key)
                    logging.info(f'Indexing {key} field')

            logging.info(f'Inserted ID: {result.inserted_id}')
        except Exception as e:
            logging.error(f'[-] Error inserting document into database\n {e}')

    def find_documents(self, collection_name, query={}, limit: int = None):
        # if limit is None, default to 5
        if limit is None:
            limit = 5
        try:
            collection = self.db[collection_name]
            return list(collection.find(query).limit(limit))
        except Exception as e:
            logging.error(f'[-] Error retrieving documents from database\n {e}')

    def update_document(self, collection_name, query, update_data, option):
        try:
            # Sanitize input
            sanitized_update_data = self.sanitize_input(update_data)

            collection = self.db[collection_name]
            collection.update_one(query, {option: sanitized_update_data})
        except Exception as e:
            logging.error(f'[-] Error updating document in database\n {e}')

    def delete_documents(self, collection_name, query):
        try:
            collection = self.db[collection_name]
            collection.delete_one(query)
        except Exception as e:
            logging.error(f'[-] Error deleting document in database\n {e}')
