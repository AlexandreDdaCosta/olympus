#!/usr/bin/env python3

import json, sys, unittest

import olympus.securities.equities.data.price as price
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
        self.adjustments = price.Adjustments(username)

    def test_symbol(self):
        with self.assertRaises(SymbolNotFoundError):
            symbol = self.symbols.get_symbol(TEST_SYMBOL_FAKE)
        symbol = self.symbols.get_symbol(TEST_SYMBOL_DIVSPLIT)
        self.assertEqual(symbol['Symbol'], TEST_SYMBOL_DIVSPLIT)
        # These checks verify that our test symbols are still valid
        dividends = self.adjustments.dividends(TEST_SYMBOL_DIV)
        self.assertIsNotNone(dividends)
        splits = self.adjustments.splits(TEST_SYMBOL_DIV)
        self.assertIsNone(splits)
        dividends = self.adjustments.dividends(TEST_SYMBOL_SPLIT)
        self.assertIsNone(dividends)
        splits = self.adjustments.splits(TEST_SYMBOL_SPLIT)
        self.assertIsNotNone(splits)
        dividends = self.adjustments.dividends(TEST_SYMBOL_DIVSPLIT)
        self.assertIsNotNone(dividends)
        splits = self.adjustments.splits(TEST_SYMBOL_DIVSPLIT)
        self.assertIsNotNone(splits)
        dividends = self.adjustments.dividends(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(dividends)
        splits = self.adjustments.splits(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(splits)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
