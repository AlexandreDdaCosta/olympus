#!/usr/bin/env python3

import json, sys, unittest

import olympus.securities.equities.data.symbols as symbols
import olympus.testing as testing

from olympus import USER
from olympus.securities.equities import *
from olympus.securities.equities.data.symbols import SymbolNotFoundError

# Standard run parameters:
# sudo su -s /bin/bash -c '... symbols.py' USER
# Optionally:
# '... symbols.py <current_run_username>'

class TestSymbols(testing.Test):

    def setUp(self):
        if len(sys.argv) == 2:
            username = self.validRunUser(sys.argv[1])
        else:
            username = self.validRunUser(USER)
        self.symbols = symbols.Read(username)

    def test_symbol(self):
        with self.assertRaises(SymbolNotFoundError):
            symbol = self.symbols.get_symbol(TEST_SYMBOL_FAKE)
        symbol = self.symbols.get_symbol(TEST_SYMBOL_ONE)
        self.assertEqual(symbol['Symbol'], TEST_SYMBOL_ONE)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
