#!/usr/bin/env python3

import json, unittest

import olympus.equities_us.data.price as price
import olympus.testing as testing

from olympus.equities_us import *

class TestPrice(testing.Test):

    def setUp(self):
        self.quote = price.Quote()

    def test_daily(self):
        quotes = self.quote.Daily(TEST_SYMBOL_ONE)
        print(json.dumps(quotes,indent=4,sort_keys=True))

    def test_intra_day(self):
        quote = self.quote.IntraDay(TEST_SYMBOL_ONE)
        print(json.dumps(quote,indent=4,sort_keys=True))

    def test_real_time(self):
        quote = self.quote.RealTime(TEST_SYMBOL_ONE)
        print(json.dumps(quote,indent=4,sort_keys=True))
        self.assertEqual(quote['Stock Quotes'][0]['1. symbol'].upper(),TEST_SYMBOL_ONE.upper(),'Returned symbol should match requested.')
        self.assertTrue(quote['Stock Quotes'][0]['3. volume'].isdigit,'Volume is not indicated by an integer, single quote')
        self.assertIsFloat(quote['Stock Quotes'][0]['2. price'],'Price in single quote has an invalid format')
        quotes = self.quote.RealTime([TEST_SYMBOL_ONE,TEST_SYMBOL_TWO])
        print(json.dumps(quotes,indent=4,sort_keys=True))
        self.assertEqual(quotes['Stock Quotes'][0]['1. symbol'].upper(),TEST_SYMBOL_ONE.upper(),'First returned symbol should match requested.')
        self.assertTrue(quotes['Stock Quotes'][0]['3. volume'].isdigit,'Volume is not indicated by an integer, first quote of two')
        self.assertIsFloat(quotes['Stock Quotes'][0]['2. price'],'First security price has an invalid format')
        self.assertEqual(quotes['Stock Quotes'][1]['1. symbol'].upper(),TEST_SYMBOL_TWO.upper(),'Second returned symbol should match requested.')
        self.assertTrue(quotes['Stock Quotes'][1]['3. volume'].isdigit,'Volume is not indicated by an integer, second quote of two')
        self.assertIsFloat(quotes['Stock Quotes'][1]['2. price'],'Second security price has an invalid format')

if __name__ == '__main__':
	unittest.main()
