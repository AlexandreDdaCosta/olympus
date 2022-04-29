# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

import ast, pymongo

from olympus import MONGO_URL

def insert_object(database,collection,datasource_name,key_name,key,issue_epoch_date,object):
    f = open("/tmp/narfie", "a")
    f.write('TEST1')
    f.write(database)
    f.write(collection)
    f.write(datasource_name)
    f.write(key_name)
    f.write(key)
    f.write(str(issue_epoch_date))
    f.write(object)
    # object: [{ "DataSource": {{ datasource_name }}, "KeyName": {{ datasource['KeyName'] }}, "Key": {{ datasource['Key'] }}, "IssueEpochDate": {{ datasource['IssueEpochDate'] }} }]
    client = pymongo.MongoClient(MONGO_URL)
    db = client[database]
    coll = db[collection]
    record = ast.literal_eval(object)
    f.write(str(record))
    f.write(type(record))
    recid = coll.insert_one(record)
    f.write(str(recid))
    f.close()
    return True

def remove_object(database,collection,datasource_name,query):
    f = open("/tmp/narfie", "a")
    f.write('TEST2')
    f.write(database)
    f.write(collection)
    f.write(datasource_name)
    f.write(query)
    f.close()
    # query: [{ "DataSource": {{ datasource_name }} }]
    return True
