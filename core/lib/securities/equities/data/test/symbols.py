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
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            self.symbols.get_symbol(TEST_SYMBOL_FAKE)
        result = self.symbols.get_symbol(TEST_SYMBOL_DIVSPLIT)
        attributes = result.list()
        for attribute in attributes:
            result.get(attribute)
        self.assertEqual(result.exchange, TEST_SYMBOL_DIVSPLIT_EXCHANGE)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.security_class, SECURITY_CLASS_STOCK)
        self.assertEqual(result.symbol, TEST_SYMBOL_DIVSPLIT)
        result = self.symbols.get_symbol(TEST_SYMBOL_ETF)
        attributes = result.list()
        for attribute in attributes:
            result.get(attribute)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.security_class, SECURITY_CLASS_ETF)
        self.assertEqual(result.symbol, TEST_SYMBOL_ETF)
        result = self.symbols.get_symbol(TEST_SYMBOL_INDEX)
        attributes = result.list()
        for attribute in attributes:
            result.get(attribute)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.security_class, INDEX_CLASS)
        self.assertEqual(result.symbol, TEST_SYMBOL_INDEX)

    def test_symbols(self):
        return #ALEX
        # Multiple symbols, including unknown/invalid
        # Note that symbol_result is the same object returned by get_symbol
        with self.assertRaises(Exception):
            self.symbols.get_symbols(TEST_SYMBOL_ETF)
        result = self.symbols.get_symbols([ TEST_SYMBOL_ETF ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNone(result.unknown_symbols)
        symbol_result = result.get_symbol(TEST_SYMBOL_ETF)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_ETF)
        result = self.symbols.get_symbols([ TEST_SYMBOL_SPLIT ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_ETF))
        symbol_result = result.get_symbol(TEST_SYMBOL_SPLIT)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_SPLIT)
        result = self.symbols.get_symbols([ TEST_SYMBOL_DIV, TEST_SYMBOL_FAKE ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_SPLIT))
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNotNone(result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        self.assertFalse(TEST_SYMBOL_DIV in result.unknown_symbols)
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        symbol_result = result.get_symbol(TEST_SYMBOL_DIV)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_DIV)
        result = self.symbols.get_symbols([ TEST_SYMBOL_DIV, TEST_SYMBOL_SPLIT ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNone(result.unknown_symbols)
        # These tests assume different exchanges for the two test symbols
        symbol_result = result.get_by_attribute('exchange',TEST_SYMBOL_DIV_EXCHANGE)
        self.assertEqual(symbol_result.symbol,TEST_SYMBOL_DIV)
        symbol_result = result.get_by_attribute('exchange',TEST_SYMBOL_SPLIT_EXCHANGE)
        self.assertEqual(symbol_result.symbol,TEST_SYMBOL_SPLIT)
        # These tests assume the same exchange for the two test symbols
        result = self.symbols.get_symbols([ TEST_SYMBOL_DIVSPLIT, TEST_SYMBOL_SPLIT ])
        symbol_result = result.get_by_attribute('exchange',NASDAQ)
        self.assertTrue(len(symbol_result) == 2)
        self.assertXor(symbol_result[0].symbol == TEST_SYMBOL_DIVSPLIT,symbol_result[1].symbol == TEST_SYMBOL_DIVSPLIT)
        self.assertXor(symbol_result[0].symbol == TEST_SYMBOL_SPLIT,symbol_result[1].symbol == TEST_SYMBOL_SPLIT)
        symbol_result = result.get_symbol(TEST_SYMBOL_DIVSPLIT)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_DIVSPLIT)
        symbol_result = result.get_symbol(TEST_SYMBOL_SPLIT)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_SPLIT)
        result = self.symbols.get_symbols([ TEST_SYMBOL_FAKE ])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNotNone(result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)

    def test_test_symbols(self):
        # These checks verify that our test symbols are still valid based on the
        # existence of dividends or splits
        dividends = self.adjustments.dividends(TEST_SYMBOL_DIV)
        self.assertIsNotNone(dividends.first())
        splits = self.adjustments.splits(TEST_SYMBOL_DIV)
        self.assertIsNone(splits.first())
        dividends = self.adjustments.dividends(TEST_SYMBOL_SPLIT)
        self.assertIsNone(dividends.first())
        splits = self.adjustments.splits(TEST_SYMBOL_SPLIT)
        self.assertIsNotNone(splits.first())
        dividends = self.adjustments.dividends(TEST_SYMBOL_DIVSPLIT)
        self.assertIsNotNone(dividends.first())
        splits = self.adjustments.splits(TEST_SYMBOL_DIVSPLIT)
        self.assertIsNotNone(splits.first())
        dividends = self.adjustments.dividends(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(dividends.first())
        splits = self.adjustments.splits(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(splits.first())

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
