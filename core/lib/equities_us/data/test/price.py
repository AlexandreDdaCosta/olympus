#!/usr/bin/env python3

import json, unittest

import olympus.equities_us.data.price as price
import olympus.testing as testing

from olympus.equities_us import *

class TestPrice(testing.Test):

    def setUp(self):
        self.quote = price.Quote()

    def test_daily(self):
        #quotes = self.quote.daily(TEST_SYMBOL_ONE)
        #print(json.dumps(quotes,indent=4,sort_keys=True))
        quotes = self.quote.daily(TEST_SYMBOL_ONE,regen=True)
        print(json.dumps(quotes,indent=4,sort_keys=True))
"""
    def test_intra_day(self):
        quote = self.quote.intraday(TEST_SYMBOL_ONE)
        print(json.dumps(quote,indent=4,sort_keys=True))
"""

if __name__ == '__main__':
	unittest.main()
