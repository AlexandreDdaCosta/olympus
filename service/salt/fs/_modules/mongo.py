# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

import ast, pymongo

from olympus import MONGO_URL

def insert_object(database,collection,datasource_name,key_name,key,issue_epoch_date,object):
    f = open("/tmp/narfie", "a")
    f.write('TEST1\n')
    f.write(object+'\n')
    client = pymongo.MongoClient(MONGO_URL)
    db = client[database]
    coll = db[collection]
    record = ast.literal_eval(object)
    f.write(str(record)+'\n')
    f.write(str(type(record))+'\n')
    #recid = coll.insert_one(record)
    f.write(str(recid)+'\n')
    f.close()
    return True

def remove_object(database,collection,datasource_name,key_name,query):
    client = pymongo.MongoClient(MONGO_URL)
    db = client[database]
    coll = db[collection]
    record = ast.literal_eval(query)
    recid = coll.delete_one(record)
    return True
