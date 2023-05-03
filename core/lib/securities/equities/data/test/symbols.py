#!/usr/bin/env python3

import json
import sys
import unittest

import olympus.securities.equities.data.price as price
import olympus.securities.equities.data.symbols as symbols
import olympus.testing as testing

from datetime import datetime as dt

from olympus import USER
from olympus.redis import Connection
from olympus.securities.equities import *
from olympus.securities.equities.data.symbols import SymbolNotFoundError

# Standard run parameters:
# sudo su -s /bin/bash -c '... symbols.py' USER


class TestSymbols(testing.Test):

    def __init__(self, test_case):
        super(TestSymbols, self).__init__(test_case)
        self.symbols = symbols.Read(self.username)

    def test_symbol(self):
        if self.skip_test():
            return
        self.print_test('Individual symbols from backend')
        with self.assertRaises(SymbolNotFoundError):
            self.symbols.get_symbol(TEST_SYMBOL_FAKE)
        result = self.symbols.get_symbol(TEST_SYMBOL_DIVSPLIT)
        attributes = result.list()
        for attribute in attributes:
            if attribute == 'watchlists':
                self.assertEqual(type(result.watchlists), list)
            result.get(attribute)
        self.assertEqual(result.exchange, TEST_SYMBOL_DIVSPLIT_EXCHANGE)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.security_class, SECURITY_CLASS_STOCK)
        self.assertEqual(result.symbol, TEST_SYMBOL_DIVSPLIT)
        result = self.symbols.get_symbol(TEST_SYMBOL_ETF)
        self.assertEqual(type(result.watchlists), list)
        attributes = result.list()
        for attribute in attributes:
            if attribute == 'watchlists':
                self.assertEqual(type(result.watchlists), list)
            result.get(attribute)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.security_class, SECURITY_CLASS_ETF)
        self.assertEqual(result.symbol, TEST_SYMBOL_ETF)
        result = self.symbols.get_symbol(TEST_SYMBOL_INDEX)
        attributes = result.list()
        for attribute in attributes:
            if attribute == 'watchlists':
                self.assertEqual(type(result.watchlists), list)
            result.get(attribute)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.security_class, INDEX_CLASS)
        self.assertEqual(result.symbol, TEST_SYMBOL_INDEX)
        redis_connection = Connection(self.username)
        redis_client = redis_connection.client()
        redis_time = redis_client.hget('securities:equities:symbol:' +
                                       TEST_SYMBOL_INDEX,
                                       'Time')
        pre_reset_time = dt.strptime(redis_time, "%Y-%m-%d %H:%M:%S.%f%z")
        result = self.symbols.get_symbol(TEST_SYMBOL_INDEX, reset=True)
        self.assertIsNotNone(result.name)
        self.assertEqual(result.security_class, INDEX_CLASS)
        self.assertEqual(result.symbol, TEST_SYMBOL_INDEX)
        redis_time = redis_client.hget('securities:equities:symbol:' +
                                       TEST_SYMBOL_INDEX,
                                       'Time')
        post_reset_time = dt.strptime(redis_time, "%Y-%m-%d %H:%M:%S.%f%z")
        self.assertGreater(post_reset_time, pre_reset_time)

    def test_symbols(self):
        if self.skip_test():
            return
        self.print_test('Symbol sets from backend')
        self.print('Multiple symbols, including unknown/invalid.')
        # Note that symbol_result is the same object returned by get_symbol
        with self.assertRaises(Exception):
            self.symbols.get_symbols(TEST_SYMBOL_ETF)
        result = self.symbols.get_symbols([TEST_SYMBOL_ETF])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNone(result.unknown_symbols)
        symbol_result = result.get_symbol(TEST_SYMBOL_ETF)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_ETF)
        result = self.symbols.get_symbols([TEST_SYMBOL_SPLIT])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_ETF))
        symbol_result = result.get_symbol(TEST_SYMBOL_SPLIT)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_SPLIT)
        result = self.symbols.get_symbols([TEST_SYMBOL_DIV, TEST_SYMBOL_FAKE])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_SPLIT))
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNotNone(result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        self.assertFalse(TEST_SYMBOL_DIV in result.unknown_symbols)
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        symbol_result = result.get_symbol(TEST_SYMBOL_DIV)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_DIV)
        result = self.symbols.get_symbols([TEST_SYMBOL_DIV, TEST_SYMBOL_SPLIT])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNone(result.unknown_symbols)

        # These tests assume different exchanges for the two test symbols

        symbol_result = result.get_by_attribute('exchange',
                                                TEST_SYMBOL_DIV_EXCHANGE)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_DIV)
        symbol_result = result.get_by_attribute('exchange',
                                                TEST_SYMBOL_SPLIT_EXCHANGE)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_SPLIT)

        # These tests assume the same exchange for the two test symbols

        result = self.symbols.get_symbols([TEST_SYMBOL_DIVSPLIT,
                                          TEST_SYMBOL_SPLIT])
        symbol_result = result.get_by_attribute('exchange', NASDAQ)
        self.assertTrue(len(symbol_result) == 2)
        self.assertXor(symbol_result[0].symbol == TEST_SYMBOL_DIVSPLIT,
                       symbol_result[1].symbol == TEST_SYMBOL_DIVSPLIT)
        self.assertXor(symbol_result[0].symbol == TEST_SYMBOL_SPLIT,
                       symbol_result[1].symbol == TEST_SYMBOL_SPLIT)
        symbol_result = result.get_symbol(TEST_SYMBOL_DIVSPLIT)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_DIVSPLIT)
        symbol_result = result.get_symbol(TEST_SYMBOL_SPLIT)
        self.assertEqual(symbol_result.symbol, TEST_SYMBOL_SPLIT)
        result = self.symbols.get_symbols([TEST_SYMBOL_FAKE])
        self.assertIsNone(result.get_symbol(TEST_SYMBOL_FAKE))
        self.assertIsNotNone(result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)

    def test_test_symbols(self):
        # These checks verify that our test symbols are still valid
        # based on the existence of dividends or splits
        if self.skip_test():
            return
        self.print_test('Checking continuing validity of test symbols')
        adjustments = price.Adjustments(self.username)
        self.print('Dividend symbol [' + TEST_SYMBOL_DIV + '].')
        dividends = adjustments.dividends(TEST_SYMBOL_DIV)
        self.assertIsNotNone(dividends.first())
        splits = adjustments.splits(TEST_SYMBOL_DIV)
        self.assertIsNone(splits.first())
        self.print('Split symbol [' + TEST_SYMBOL_SPLIT + '].')
        dividends = adjustments.dividends(TEST_SYMBOL_SPLIT)
        self.assertIsNone(dividends.first())
        splits = adjustments.splits(TEST_SYMBOL_SPLIT)
        self.assertIsNotNone(splits.first())
        self.print('Split + dividend symbol [' + TEST_SYMBOL_DIVSPLIT + '].')
        dividends = adjustments.dividends(TEST_SYMBOL_DIVSPLIT)
        self.assertIsNotNone(dividends.first())
        splits = adjustments.splits(TEST_SYMBOL_DIVSPLIT)
        self.assertIsNotNone(splits.first())
        self.print('No split / no dividend symbol [' +
                   TEST_SYMBOL_NODIVSPLIT +
                   '].')
        dividends = adjustments.dividends(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(dividends.first())
        splits = adjustments.splits(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(splits.first())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        unittest.main(argv=['username'])
    else:
        unittest.main()
