# Core procedures for MongoDB

import pymongo

from os import access, R_OK
from os.path import isfile

from olympus import MONGO_ADMIN_USERNAME, MONGO_URL, USER_ETC

def MONGO_USER_PASSWORD_FILE(user=MONGO_ADMIN_USERNAME):
    return USER_ETC(user) + 'mongodb_password'
def MONGO_USER_OLD_PASSWORD_FILE(user=MONGO_ADMIN_USERNAME):
    return USER_ETC(user) + 'mongodb_password.old'

class UserCredentials():

    def __init__(self,user):
        self.user=user
        self.password_file = MONGO_USER_PASSWORD_FILE(self.user)
        self.password_file_old = MONGO_USER_OLD_PASSWORD_FILE(self.user)

    def is_secured(self):
        if isfile(self.password_file) and access(self.password_file, R_OK):
            with open(self.password_file) as f:
                self.password = f.readline().rstrip()
            f.close()
            if self.password == '':
                raise Exception('Password file '+self.password_file+' for user '+self.user+' exists and is readable but is empty.')
            return True
        else:
            # We assume the user is not secured. We may be calling this procedure with a bad user, in which case exceptions may follow.
            return False

    def rotate_password_file(password):
        pass

class Connection(UserCredentials):

    def __init__(self,user=MONGO_ADMIN_USERNAME):
        super(Connection,self).__init__(user)
        self.user = user

    def connect(self,database=None,collection=None):
        if self.is_secured():
            self.client = pymongo.MongoClient(MONGO_URL,username=self.user,password=self.password)
        else:
            self.client = pymongo.MongoClient(MONGO_URL)
        if database is not None:
            db = self.client[database]
            if collection is not None:
                return db[collection]
            else:
                return db
        else:
            return self.client
