# Core procedures for MongoDB

import os, pymongo, shutil, stat

from os.path import isfile

from olympus import MONGO_ADMIN_USERNAME, MONGO_URL, USER_ETC

def MONGO_USER_PASSWORD_FILE(user=MONGO_ADMIN_USERNAME):
    return USER_ETC(user) + 'mongodb_password'
def MONGO_USER_OLD_PASSWORD_FILE(user=MONGO_ADMIN_USERNAME):
    return USER_ETC(user) + 'mongodb_password.old'

class UserCredentials():

    def __init__(self,user):
        self.user=user
        self.password_file = MONGO_USER_PASSWORD_FILE(user)
        self.password_file_old = MONGO_USER_OLD_PASSWORD_FILE(user)

    def existing_password(self,user=None):
        if user is None:
            user=self.user
            password_file = self.password_file
        else:
            password_file = MONGO_USER_PASSWORD_FILE(user)
        if isfile(password_file):
            shutil.chown(password_file,self.user,self.user)
            os.chmod(password_file,stat.S_IREAD | stat.S_IWRITE)
            with open(password_file,'r') as f:
                password = f.readline().rstrip()
            f.close()
            if password == '':
                raise Exception('Password file '+password_file+' for user '+self.user+' exists and is readable but is empty.')
            return password
        else:
            # We assume the user is not secured. Calling this procedure with a unprivileged user may lead to exceptions.
            return None

    def rotate_password_file(self,password,user=None):
        if user is None:
            user=self.user
            password_file = self.password_file
            password_file_old = self.password_file_old
        else:
            password_file = MONGO_USER_PASSWORD_FILE(user)
            password_file_old = MONGO_USER_OLD_PASSWORD_FILE(user)
        with open('/tmp/pymongo','a') as f:
            f.write('USER\n'+user+'\n')
            f.close()
        existing_password = None
        old_password = None
        password_file_existed = False
        if isfile(password_file):
            password_file_existed = True
            shutil.chown(password_file,user,user)
            os.chmod(password_file,stat.S_IREAD | stat.S_IWRITE)
            with open(password_file,'r') as f:
                existing_password = f.readline().rstrip()
            f.close()
        if isfile(password_file_old):
            shutil.chown(password_file_old,user,user)
            os.chmod(password_file_old,stat.S_IREAD | stat.S_IWRITE)
            with open(password_file_old,'r') as f:
                old_password = f.readline().rstrip()
            f.close()
        if existing_password is not None:
            with open(password_file_old,'w') as f:
                f.write(existing_password)
                f.truncate()
                f.close()
            shutil.chown(password_file_old,user,user)
            os.chmod(password_file_old,stat.S_IREAD | stat.S_IWRITE)
        with open(password_file,'w') as f:
            f.write(password)
            f.truncate()
            f.close()
        if not password_file_existed:
            shutil.chown(password_file,user,user)
            os.chmod(password_file,stat.S_IREAD | stat.S_IWRITE)

class Connection(UserCredentials):

    def __init__(self,user=MONGO_ADMIN_USERNAME):
        super(Connection,self).__init__(user)
        self.user = user

    def connect(self,database=None,collection=None):
        password = self.existing_password()
        if password is not None:
            self.client = pymongo.MongoClient(MONGO_URL,username=self.user,password=password)
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
