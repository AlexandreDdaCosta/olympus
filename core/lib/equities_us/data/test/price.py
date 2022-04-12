#!/usr/bin/env python3

import json, unittest

import olympus.equities_us.data.price as price
import olympus.testing as testing

from olympus.equities_us import *

class TestPrice(testing.Test):

    def setUp(self):
        self.quote = price.Quote()

    def test_daily(self):
        quotes = self.quote.daily(TEST_SYMBOL_ONE)
        print(json.dumps(quotes,indent=4,sort_keys=True))

    def test_intra_day(self):
        quote = self.quote.intraday(TEST_SYMBOL_ONE)
        print(json.dumps(quote,indent=4,sort_keys=True))

    def test_real_time(self):
        quote = self.quote.real_time(TEST_SYMBOL_ONE)
        print(json.dumps(quote,indent=4,sort_keys=True))
        self.assertEqual(quote['symbol'].upper(),TEST_SYMBOL_ONE.upper(),'Returned symbol should match requested.')
        self.assertTrue(quote['volume'].isdigit,'Volume is not indicated by an integer, single quote')
        self.assertIsFloat(quote['price'],'Price in single quote has an invalid format')
        quotes = self.quote.real_time([TEST_SYMBOL_ONE,TEST_SYMBOL_TWO])
        print(json.dumps(quotes,indent=4,sort_keys=True))
        self.assertEqual(quotes[TEST_SYMBOL_ONE.upper()]['symbol'].upper(),TEST_SYMBOL_ONE.upper(),'First returned symbol should match requested.')
        self.assertTrue(quotes[TEST_SYMBOL_ONE.upper()]['volume'].isdigit,'Volume is not indicated by an integer, first quote of two')
        self.assertIsFloat(quotes[TEST_SYMBOL_ONE.upper()]['price'],'First security price has an invalid format')
        self.assertEqual(quotes[TEST_SYMBOL_TWO.upper()]['symbol'].upper(),TEST_SYMBOL_TWO.upper(),'Second returned symbol should match requested.')
        self.assertTrue(quotes[TEST_SYMBOL_TWO.upper()]['volume'].isdigit,'Volume is not indicated by an integer, second quote of two')
        self.assertIsFloat(quotes[TEST_SYMBOL_TWO.upper()]['price'],'Second security price has an invalid format')

if __name__ == '__main__':
	unittest.main()
