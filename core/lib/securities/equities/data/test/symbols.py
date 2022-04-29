#!/usr/bin/env python3

import json, unittest

import olympus.securities.equities.data.symbols as symbols
import olympus.testing as testing

from olympus.securities.equities import *

class TestSymbols(testing.Test):

    def setUp(self):
        self.init = symbols.Init(verbose=True)

    def test_populate_collections(self):
        populate = self.init.populate_collections()

if __name__ == '__main__':
	unittest.main()
