#!/usr/bin/env python3

import sys
import unittest

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
        access_token = self.connector.token()
        print(access_token)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
