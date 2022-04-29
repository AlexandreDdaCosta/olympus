# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

import ast, pymongo

from olympus import MONGO_URL

def insert_object(database,collection,datasource_name,key_name,key,issue_epoch_date,object):
    client = pymongo.MongoClient(MONGO_URL)
    db = client[database]
    coll = db[collection]
    #recid = coll.insert_one(object)
    return True

def remove_object(database,collection,datasource_name,key_name,query):
    client = pymongo.MongoClient(MONGO_URL)
    db = client[database]
    coll = db[collection]
    recid = coll.delete_one(query)
    return True
