# -*- coding: utf-8 -*-

'''
Tools for handling MongoDB operations
'''

import argon2, datetime, hashlib
import olympus.mongodb as mongodb

from olympus import ARGON2_CONFIG, MONGODB_SERVICE, RESTAPI_RUN_USERNAME, USER, User
from olympus.mongodb import MONGO_ADMIN_USERNAME

def insert_object(database,collection,object,user=USER):
    connector = mongodb.Connection(user)
    coll = connector.connect(database,collection)
    recid = coll.insert_one(object)
    return True

def insert_update_restapi_user(username,password,defined_routes=None):
    # Hashing parameters based on OWASP cheat sheet recommendations (as of March 2022)
    argon2Hasher = argon2.PasswordHasher(memory_cost=ARGON2_CONFIG['memory_cost'], parallelism=ARGON2_CONFIG['parallelism'], salt_len=ARGON2_CONFIG['salt_bytes'], time_cost=ARGON2_CONFIG['time_cost'])
    hashed_password = argon2Hasher.hash(password)
    connector = mongodb.Connection(RESTAPI_RUN_USERNAME)
    database_name = connector.user_database_name()
    collection = connector.connect(database_name,'auth_users')
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
    manager = mongodb.Connection(MONGO_ADMIN_USERNAME)
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
    connector = mongodb.Connection(MONGO_ADMIN_USERNAME)
    database = connector.connect('admin')
    user_entry=database['system.users'].find_one({"user":username},{'_id':0, 'user':1})
    user_object = User(username)
    user_object.rotate_service_password_file(MONGODB_SERVICE,password)
    if user_entry is not None:
        database.command('updateUser',username,pwd=password,roles=roles)
    else:
        database.command('createUser',username,pwd=password,roles=roles)
    return True
