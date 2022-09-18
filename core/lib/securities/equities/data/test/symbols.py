#!/usr/bin/env python3

import json, sys, unittest

import olympus.securities.equities.data.price as price
import olympus.securities.equities.data.symbols as symbols
import olympus.testing as testing

from olympus import USER
from olympus.securities import SECURITY_STANDARD_ATTRIBUTES
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
            self.symbols.get_symbol(TEST_SYMBOL_FAKE)
        result = self.symbols.get_symbol(TEST_SYMBOL_DIVSPLIT)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.symbol, TEST_SYMBOL_DIVSPLIT)
        self.assertEqual(result.security_class, SECURITY_CLASS_STOCK)
        result = self.symbols.get_symbol(TEST_SYMBOL_ETF)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.symbol, TEST_SYMBOL_ETF)
        self.assertEqual(result.security_class, SECURITY_CLASS_ETF)
        result = self.symbols.get_symbol(TEST_SYMBOL_INDEX)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.symbol, TEST_SYMBOL_INDEX)
        self.assertEqual(result.security_class, INDEX_CLASS)

    def test_symbols(self):
        # Multiple symbols, including unknown/invalid
        with self.assertRaises(Exception):
            self.symbols.get_symbols(TEST_SYMBOL_ETF)
        result = self.symbols.get_symbols([ TEST_SYMBOL_ETF ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNone(result.unknown_symbols)
        #ALEX Add method to get all standard, adjusted, and misc attributes
        symbol_result = result.get_symbol(TEST_SYMBOL_ETF)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_ETF)
        self.assertEqual(symbol_result.security_class, SECURITY_CLASS_ETF)
        result = self.symbols.get_symbols([ TEST_SYMBOL_SPLIT ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_ETF))
        symbol_result = result.get_symbol(TEST_SYMBOL_SPLIT)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_SPLIT)
        self.assertEqual(symbol_result.security_class, SECURITY_CLASS_STOCK)

        result = self.symbols.get_symbols([ TEST_SYMBOL_DIV, TEST_SYMBOL_FAKE ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_SPLIT))
        self.assertIsNotNone(result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))

        result = self.symbols.get_symbols([ TEST_SYMBOL_DIVSPLIT, TEST_SYMBOL_NODIVSPLIT ])

        result = self.symbols.get_symbols([ TEST_SYMBOL_DIV, TEST_SYMBOL_FAKE ])
        with self.assertRaises(Exception):
            self.symbols.get_symbols(TEST_SYMBOL_FAKE)

        result = self.symbols.get_symbols([ TEST_SYMBOL_FAKE ])

    def test_test_symbols(self):
        return #ALEX
        # These checks verify that our test symbols are still valid based on the
        # existence of dividends or splits
        self.assertIsNotNone(self.adjustments.dividends(TEST_SYMBOL_DIV))
        self.assertIsNone(self.adjustments.splits(TEST_SYMBOL_DIV))
        self.assertIsNone(self.adjustments.dividends(TEST_SYMBOL_SPLIT))
        self.assertIsNotNone(self.adjustments.splits(TEST_SYMBOL_SPLIT))
        self.assertIsNotNone(self.adjustments.dividends(TEST_SYMBOL_DIVSPLIT))
        self.assertIsNotNone(self.adjustments.splits(TEST_SYMBOL_DIVSPLIT))
        self.assertIsNone(self.adjustments.dividends(TEST_SYMBOL_NODIVSPLIT))
        self.assertIsNone(self.adjustments.splits(TEST_SYMBOL_NODIVSPLIT))

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
