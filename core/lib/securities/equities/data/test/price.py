#!/usr/bin/env python3

import json, sys, unittest

from olympus import USER
from olympus.securities.equities.data.symbols import SymbolNotFoundError

import olympus.securities.equities.data as data
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
        self.daily = price.Daily(username)
        self.intraday = price.Intraday(username)
        self.latest = price.Latest(username)
        self.mongo_data = data.Connection(username)

    def test_daily(self):
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.daily.quote(TEST_SYMBOL_FAKE)
        quotes = self.daily.quote(TEST_SYMBOL_ONE,regen=True)
        # Remove the last price record by date, then get the quote again. Check that the record was restored.
        price_collection = 'price.' + TEST_SYMBOL_ONE
        collection = self.mongo_data.db[price_collection]
        interval_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0 })
        last_date = None
        previous_date = None
        for quote_date in interval_data['Quotes']:
            previous_date = last_date
            if last_date is None or last_date < quote_date:
                last_date = quote_date
        if previous_date is not None:
            last_quote_saved = interval_data['Quotes'][last_date]
            # Test for proper regeneration of missing dates by simulating the result from one day ago after doing full regen
            year,month,day = map(int,previous_date.split('-'))
            time_string = "%d-%02d-%02d 00:00:00.000000-04:00" % (year,month,day)
            collection.update_one({ 'Interval': '1d' },{ "$unset": { 'Quotes.'+last_date: 1 }})
            collection.update_one({ 'Interval': '1d' },{ "$set":  { 'End Date': previous_date, 'Time': time_string }})
            interval_data = collection.find_one({ 'Interval': '1d',  },{ '_id': 0, 'Interval': 0 })
            self.assertTrue(previous_date in interval_data['Quotes']);
            self.assertFalse(last_date in interval_data['Quotes']);
            quotes_noregen = self.daily.quote(TEST_SYMBOL_ONE)
            self.assertTrue(last_date in quotes_noregen);
            for key in last_quote_saved:
                self.assertTrue(last_quote_saved[key] == quotes_noregen[last_date][key])
    
    def test_latest(self):
        # "quotekeys" not a comprehensive list; only thekey price items get verified
        quotekeys = ['symbol','description','bidPrice','bidSize','askPrice','askSize','lastPrice','lastSize','openPrice','highPrice','lowPrice','closePrice','netChange','totalVolume']
        quote = self.latest.quote(TEST_SYMBOL_ONE)
        self.assertTrue('quotes' in quote)
        self.assertTrue(TEST_SYMBOL_ONE in quote['quotes'])
        self.assertEqual(quote['quotes'][TEST_SYMBOL_ONE]['symbol'], TEST_SYMBOL_ONE)
        for key in quotekeys:
            self.assertTrue(key in quote['quotes'][TEST_SYMBOL_ONE])
        quote = self.latest.quote([TEST_SYMBOL_ONE.lower(),TEST_SYMBOL_TWO,TEST_SYMBOL_FAKE.lower()])
        self.assertTrue('quotes' in quote)
        self.assertTrue(TEST_SYMBOL_ONE.upper() in quote['quotes'])
        self.assertEqual(quote['quotes'][TEST_SYMBOL_ONE.upper()]['symbol'], TEST_SYMBOL_ONE.upper())
        for key in quotekeys:
            self.assertTrue(key in quote['quotes'][TEST_SYMBOL_ONE.upper()])
        self.assertTrue(TEST_SYMBOL_TWO in quote['quotes'])
        self.assertEqual(quote['quotes'][TEST_SYMBOL_TWO]['symbol'], TEST_SYMBOL_TWO)
        for key in quotekeys:
            self.assertTrue(key in quote['quotes'][TEST_SYMBOL_TWO])
        self.assertTrue(TEST_SYMBOL_FAKE.upper() in quote['unknown_symbols'])
        quote = self.latest.quote([TEST_SYMBOL_FAKE,TEST_SYMBOL_FAKE_TWO.lower()])
        self.assertFalse('quotes' in quote)
        self.assertTrue(TEST_SYMBOL_FAKE in quote['unknown_symbols'])
        self.assertTrue(TEST_SYMBOL_FAKE_TWO.upper() in quote['unknown_symbols'])

    def test_intra_day(self):
        return # ALEX
        quotes = self.intraday.quote(TEST_SYMBOL_ONE)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
