#!/usr/bin/env python3

import json, unittest

import olympus.projects.ploutos.data.price as price
import olympus.testing as testing

from olympus.projects.ploutos import *

class TestPrice(testing.Test):

    def setUp(self):
        self.quote = price.Quote()

    def test_daily(self):
        #quotes = self.quote.Daily(TEST_SYMBOL_ONE)
        quotes = self.quote.Daily('AAPL')
        print(json.dumps(quotes,indent=4,sort_keys=True))

    def test_intra_day(self):
        quote = self.quote.IntraDay(TEST_SYMBOL_ONE)
        #print(json.dumps(quote,indent=4,sort_keys=True))

    def test_real_time(self):
        quote = self.quote.RealTime(TEST_SYMBOL_ONE)[0]
        self.assertEqual(quote['t'].upper(),TEST_SYMBOL_ONE.upper(),'Returned symbol should match requested.')
        self.assertEqual(quote['e'].upper(),TEST_SYMBOL_ONE_EXCHANGE.upper(),'Returned exchange should match requested.')
        quotes = self.quote.RealTime([TEST_SYMBOL_ONE,TEST_SYMBOL_TWO])
        self.assertEqual(quotes[0]['t'].upper(),TEST_SYMBOL_ONE.upper(),'First returned symbol should match first requested.')
        self.assertEqual(quotes[0]['e'].upper(),TEST_SYMBOL_ONE_EXCHANGE.upper(),'First returned exchange should match first requested.')
        self.assertEqual(quotes[1]['t'].upper(),TEST_SYMBOL_TWO.upper(),'Second returned symbol should match second requested.')
        self.assertEqual(quotes[1]['e'].upper(),TEST_SYMBOL_TWO_EXCHANGE.upper(),'Second returned exchange should match second requested.')

if __name__ == '__main__':
	unittest.main()
