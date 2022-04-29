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
    #record = ast.literal_eval(object)
    #recid = coll.insert_one(record)
    recid = coll.insert_one(object)
    return True

def remove_object(database,collection,datasource_name,key_name,query):
    f = open("/tmp/narfie", "a")
    f.write('TEST1\n')
    client = pymongo.MongoClient(MONGO_URL)
    db = client[database]
    coll = db[collection]
    f.write(str(query)+'\n')
    #record = ast.literal_eval(query)
    #f.write(str(record)+'\n')
    #f.write(str(type(record))+'\n')
    #recid = coll.delete_one(record)
    recid = coll.delete_one(query)
    f.close()
    return True
