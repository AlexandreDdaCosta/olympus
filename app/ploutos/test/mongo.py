#!/usr/bin/env python3

import pymongo, unittest

import olympus.testing as testing

from olympus import CAFILE, CERTFILE, KEYFILE, MONGO_URL

class TestMongo(testing.Test):

    def setUp(self):
        pass

    def test_connect(self):
        client = pymongo.MongoClient(MONGO_URL,ssl=True,ssl_ca_certs=CAFILE,ssl_certfile=CERTFILE,ssl_keyfile=KEYFILE,ssl_match_hostname=False)
        test_collection = client.test.pymongo_test
        test_collection.drop()
        delete_result = test_collection.delete_many({})
        self.assertEqual(delete_result.deleted_count,0,'No entries should exist in test database.')
        insert_many_result = test_collection.insert_many([{'a':1},{'a':2},{'a':3},{'a':3}])
        self.assertTrue(insert_many_result.acknowledged,'Result should be an acknowledged write operation.')
        self.assertEqual(test_collection.count_documents({}),4,'Four entries should exist in test database.')
        self.assertEqual(len(insert_many_result.inserted_ids),4,'Four entries should exist in test database.')
        self.assertEqual(test_collection.count_documents({'a': 1}),1,'One document where "a" equals "1".')
        self.assertEqual(test_collection.count_documents({'a': 3}),2,'Two documents where "a" equals "3".')
        self.assertEqual(test_collection.count_documents({'a': 4}),0,'No documents where "a" equals "4".')
        self.assertEqual(test_collection.count_documents({}),4,'Four documents in test collection.')
        test_collection.drop()

if __name__ == '__main__':
	unittest.main()
