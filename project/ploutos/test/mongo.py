#!/usr/bin/env python3

import pymongo, unittest

import olympus.testing as testing

CAFILE = '/usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt'
CERTFILE = '/etc/ssl/localcerts/client-crt.pem'
KEYFILE = '/etc/ssl/localcerts/client-key.pem'
URL = 'mongodb://zeus:27017/olympus?ssl=true';

class TestMongo(testing.Test):

    def setUp(self):
        pass

    def test_connect(self):
        client = pymongo.MongoClient(URL,ssl=True,ssl_ca_certs=CAFILE,ssl_certfile=CERTFILE,ssl_keyfile=KEYFILE)
        test_collection = client.olympus.pymongo_test
        newdoc_obj = test_collection.insert_one({'x': 1})
        print(test_collection.find({'x': 1}))
        test_collection.drop()


if __name__ == '__main__':
	unittest.main()
