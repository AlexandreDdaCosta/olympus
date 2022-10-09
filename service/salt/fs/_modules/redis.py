# -*- coding: utf-8 -*-

'''
Tools for managing redis
'''

from olympus.redis import Connection

from olympus import USER

def delete_securities_equities_symbols(user=USER):
    redis_connection = Connection(user)
    redis_client = redis_connection.client()
    for key in redis_client.scan_iter('securities:equities:symbol:*'):
        redis_client.delete(key)
    return True
