# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

import olympus.mongodb as mongodb

from olympus import MONGO_ADMIN_USERNAME, MONGO_URL

def insert_object(database,collection,object):
    connector = mongodb.Connection(user=MONGO_ADMIN_USERNAME)
    coll = connector.connect(database,collection)
    recid = coll.insert_one(object)
    return True

def purge_users(valid_users=None):
    if valid_users is None:
        valid_users = []
    manager = mongodb.Connection(user=MONGO_ADMIN_USERNAME)
    database = manager.connect('admin')
    users=database['system.users'].find({},{'_id':0, 'user':1})
    for user in users:
        if user['user'] != MONGO_ADMIN_USERNAME and user['user'] not in valid_users:
            database.command('dropUser',user['user'])
    return True

def remove_object(database,collection,query):
    connector = mongodb.Connection(user=MONGO_ADMIN_USERNAME)
    coll = connector.connect(database,collection)
    recid = coll.delete_one(query)
    return True

def user(username,password,admin=False,roles=None):
    if admin is True:
        if username != MONGO_ADMIN_USERNAME:
            roles = [{'role':'userAdminAnyDatabase','db':'admin'},{'role':'readWriteAnyDatabase','db':'admin'}]
        else:
            roles = [{'role':'userAdminAnyDatabase','db':'admin'}]
    elif roles is None:
        roles = []
    else:
        # Re-formatting roles variable from salt's jinja2 pillar declarations
        new_roles = []
        for role_ordered_dict in roles:
            for database, role in role_ordered_dict.items():
                role_dict = {'role': role, 'db': database}
                new_roles.append(role_dict)
                break
        roles = new_roles
    manager = mongodb.Connection(user=MONGO_ADMIN_USERNAME)
    database = manager.connect('admin')
    user_entry=database['system.users'].find_one({"user":username},{'_id':0, 'user':1})
    manager.rotate_password_file(password,username)
    if user_entry is not None:
        database.command('updateUser',username,pwd=password,roles=roles)
    else:
        database.command('createUser',username,pwd=password,roles=roles)
    return True
