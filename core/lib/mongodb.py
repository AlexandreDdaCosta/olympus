# Core procedures for MongoDB

import pymongo

from olympus import MONGODB_SERVICE, User

MONGO_ADMIN_USERNAME = 'mongodb'
MONGO_URL = 'mongodb://localhost:27017/'


class Connection(User):

    def __init__(self, username=MONGO_ADMIN_USERNAME):
        super(Connection, self).__init__(username)
        self.username = username

    def connect(self, database=None, collection=None):
        password = self.get_service_password(MONGODB_SERVICE)
        if password is not None:
            self.client = pymongo.MongoClient(MONGO_URL,
                                              username=self.username,
                                              password=password)
        else:
            self.client = pymongo.MongoClient(MONGO_URL)
        if database is not None:
            self.db = self.client[database]
            if collection is not None:
                return self.db[collection]
            else:
                return self.db
        else:
            return self.client

    def user_database_name(self):
        return 'user:' + self.username
