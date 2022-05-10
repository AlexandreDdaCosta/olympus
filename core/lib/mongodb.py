# Core procedures for MongoDB

import pymongo

from os import access, R_OK
from os.path import isfile

from olympus import MONGO_ADMIN_USERNAME, MONGO_URL, MONGO_USER_PASSWORD_FILE

class Connection():

    def __init__(self,user=MONGO_ADMIN_USERNAME):
        self.user = user

    def connect(self):
        file = MONGO_USER_PASSWORD_FILE(self.user)
        if isfile(file) and access(file, R_OK):
            with open(file) as f:
                password = f.readline().rstrip()
            f.close()
            self.client = pymongo.MongoClient(MONGO_URL,username=self.user,password=password)
        else:
            # We assume the database is not secured
            self.client = pymongo.MongoClient(MONGO_URL)
        return self.client
