# Core procedures for MongoDB

import pymongo

from olympus import MONGO_ADMIN_USERNAME, MONGO_URL

class Connection():

    def __init__(self,user=MONGO_ADMIN_USERNAME,**kwargs):
        self.user = user
        print(self.user)

    def connect(self):
        self.client = pymongo.MongoClient(MONGO_URL)
        return self.client
