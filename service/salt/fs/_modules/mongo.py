# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

import argon2, datetime, hashlib
import olympus.mongodb as mongodb

from olympus import ARGON2_CONFIG, MONGO_ADMIN_USERNAME, MONGO_URL, MONGO_USER_DATABASE, RESTAPI_RUN_USERNAME, USER

def alextest():
    f = open('/tmp/alextest', 'a')
    f.write('foo\n')
    f.close()
    return True

def insert_object(database,collection,object,user=USER):
    connector = mongodb.Connection(user)
    coll = connector.connect(database,collection)
    recid = coll.insert_one(object)
    return True

def insert_update_restapi_user(username,password,defined_routes=None):
    # Hashing parameters based on OWASP cheat sheet recommendations (as of March 2022)
    argon2Hasher = argon2.PasswordHasher(memory_cost=ARGON2_CONFIG['memory_cost'], parallelism=ARGON2_CONFIG['parallelism'], salt_len=ARGON2_CONFIG['salt_bytes'], time_cost=ARGON2_CONFIG['time_cost'])
    hashed_password = argon2Hasher.hash(password)
    manager = mongodb.Connection(user=RESTAPI_RUN_USERNAME)
    database = manager.connect(MONGO_USER_DATABASE(RESTAPI_RUN_USERNAME))
    collection = database['auth_users']
    find = {"Username":username}
    count = collection.count_documents(find)
    if (count == 0):
        # Insert
        object = { "Username": username, "Password": hashed_password, "LastUpdate": datetime.datetime.now(), "DefinedRoutes": defined_routes }
        collection.insert_one(object)
    else:
        # Update
        filter = { "Username": username }
        object = { "Password": hashed_password, "LastUpdate": datetime.datetime.now(), "DefinedRoutes": defined_routes }
        collection.update_one(filter, { "$set": object })
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

def remove_object(database,collection,query,user=USER):
    connector = mongodb.Connection(user)
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
