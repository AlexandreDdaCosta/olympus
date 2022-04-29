# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

def insert_object(database,collection,datasource_name,key_name,key,issue_epoch_date):
    f = open("/tmp/narfie", "a")
    f.write('TEST1')
    f.write(database)
    f.write(collection)
    f.write(datasource_name)
    f.write(key_name)
    f.write(key)
    f.write(issue_epoch_date)
    f.close()
    # object: [{ "DataSource": {{ datasource_name }}, "KeyName": {{ datasource['KeyName'] }}, "Key": {{ datasource['Key'] }}, "IssueEpochDate": {{ datasource['IssueEpochDate'] }} }]
    return True

def remove_object(database,collection,datasource_name):
    f = open("/tmp/narfie", "a")
    f.write('TEST2')
    f.write(database)
    f.write(collection)
    f.write(datasource_name)
    f.close()
    # query: [{ "DataSource": {{ datasource_name }} }]
    return True
