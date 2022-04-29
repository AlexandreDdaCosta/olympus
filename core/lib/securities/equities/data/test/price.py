#!/usr/bin/env python3

import json, sys, unittest

from olympus import USER
from olympus.securities.equities.data.symbols import SymbolNotFoundError

import olympus.securities.equities.data.price as price
import olympus.testing as testing

from olympus.securities.equities import *

# Standard run parameters:
# sudo su -s /bin/bash -c '... price.py' USER
# Optionally:
# '... price.py <current_run_username>'

class TestPrice(testing.Test):

    def setUp(self):
        if len(sys.argv) == 2:
            username = self.validRunUser(sys.argv[1])
        else:
            username = self.validRunUser(USER)
        self.quote = price.Quote(username)

    def test_daily(self):
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.quote.daily(TEST_SYMBOL_FAKE)
        quotes = self.quote.daily(TEST_SYMBOL_ONE,regen=True)
        print(json.dumps(quotes,indent=4,sort_keys=True))
        quotes = self.quote.daily(TEST_SYMBOL_ONE)
        print(json.dumps(quotes,indent=4,sort_keys=True))

    def test_intra_day(self):
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.quote.daily(TEST_SYMBOL_FAKE)
        quote = self.quote.intraday(TEST_SYMBOL_ONE)
        print(json.dumps(quote,indent=4,sort_keys=True))

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
