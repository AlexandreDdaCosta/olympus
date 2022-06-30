#!/usr/bin/env python3

import sys, unittest

import olympus.restapi as restapi
import olympus.testing as testing

from olympus import USER

# Standard run parameters:
# sudo su -s /bin/bash -c '... restapi.py' USER
# Optionally:
# '... restapi.py <current_run_username>'

class TestRestapi(testing.Test):

    def setUp(self):
        if len(sys.argv) == 2:
            self.username = self.validRunUser(sys.argv[1])
        else:
            self.username = self.validRunUser(USER)
        self.connector = restapi.Connection(self.username)

    def test_connect(self):
        access_token = self.connector.connect()

        #self.assertTrue(insert_many_result.acknowledged,'Result should be an acknowledged write operation.')
        #self.assertEqual(test_collection.count_documents({}),4,'Four entries should exist in test database.')
        #self.assertEqual(len(insert_many_result.inserted_ids),4,'Four entries should exist in test database.')

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
