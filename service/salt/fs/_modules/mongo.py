# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

import ast, pymongo

from olympus import MONGO_URL

def insert_object(database,collection,object):
    coll = _connect(database, collection)
    recid = coll.insert_one(object)
    return True

def remove_object(database,collection,query):
    coll = _connect(database, collection)
    recid = coll.delete_one(query)
    return True

def user(username,password,admin,roles=None):
    with open('/tmp/pymongo', 'a') as f:
        if roles is not None:
            for role in roles:
                f.write(str(role))
                f.write('\n')
    return True

def _connect(database,collection):
    client = pymongo.MongoClient(MONGO_URL)
    db = client[database]
    return db[collection]
