#!/usr/bin/env python3

import json, unittest

import olympus.equities_us.data.symbols_new as symbols
import olympus.testing as testing

from olympus.equities_us import *

class TestSymbols(testing.Test):

    def setUp(self):
        self.init = symbols.Init(verbose=True)

    def test_populate_collections(self):
        populate = self.init.populate_collections()

if __name__ == '__main__':
	unittest.main()
