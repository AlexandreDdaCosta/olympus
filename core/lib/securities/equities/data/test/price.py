#!/usr/bin/env python3

import json, sys, time, unittest

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
        self.adjustments = price.Adjustments(username)
        self.daily = price.Daily(username)
        self.intraday = price.Intraday(username)
        self.latest = price.Latest(username)
        self.mongo_data = data.Connection(username)

    def test_adjustments(self):
        return # ALEX
        with self.assertRaises(SymbolNotFoundError):
            splits = self.adjustments.splits(TEST_SYMBOL_FAKE)
        #splits = self.adjustments.splits(TEST_SYMBOL_TWO)
        #print(splits)
        #splits = self.adjustments.splits('ZIM',regen=True)
        #print(splits)
        #dividends = self.adjustments.dividends(TEST_SYMBOL_TWO)
        #print(dividends)
        #regen_splits = self.adjustments.splits(TEST_SYMBOL_TWO,regen=True)
        #print(regen_splits)
        #regen_dividends = self.adjustments.dividends(TEST_SYMBOL_TWO,regen=True)
        #print(regen_dividends)
        adjustments = self.adjustments.adjustments(TEST_SYMBOL_TWO,regen=True)
        print(adjustments)

    def test_daily(self):
        return # ALEX
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.daily.quote(TEST_SYMBOL_FAKE)
        #quotes = self.daily.quote(TEST_SYMBOL_TWO)
        quotes = self.daily.quote(TEST_SYMBOL_TWO,regen=True)
        #quotes = self.daily.quote(TEST_SYMBOL_TWO,regen=True,start_date='2020-08-24',end_date='2020-09-09')
        #quotes = self.daily.quote(TEST_SYMBOL_TWO,start_date='2020-08-24',end_date='2020-09-09')
        #data = json.dumps(quotes,indent=4)
        #print(data)
        # Remove the last price record by date, then get the quote again. Check that the record was restored.
        price_collection = 'price.' + TEST_SYMBOL_TWO
        collection = self.mongo_data.db[price_collection]
        interval_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0 })
        last_date = None
        previous_date = None
        for quote_date in sorted(interval_data['Quotes']):
            previous_date = last_date
            if last_date is None or last_date < quote_date:
                last_date = quote_date
        if previous_date is not None:
            last_quote_saved = interval_data['Quotes'][last_date]
            # Test for regeneration of missing dates by simulating the result from one trading day
            # previous after doing full regen
            year,month,day = map(int,previous_date.split('-'))
            time_string = "%d-%02d-%02d 00:00:00.000000-04:00" % (year,month,day)
            collection.update_one({ 'Interval': '1d' },{ "$unset": { 'Quotes.'+last_date: 1 }})
            collection.update_one({ 'Interval': '1d' },{ "$set":  { 'End Date': previous_date, 'Time': time_string }})
            interval_data = collection.find_one({ 'Interval': '1d',  },{ '_id': 0, 'Interval': 0 })
            self.assertTrue(previous_date in interval_data['Quotes']);
            self.assertFalse(last_date in interval_data['Quotes']);
            quotes_noregen = self.daily.quote(TEST_SYMBOL_TWO)
            self.assertTrue(last_date in quotes_noregen);
    
    def test_latest(self):
        # 'quoteTimeInLong': 1660953600058, 'tradeTimeInLong': 1660953596094, 'regularMarketTradeTimeInLong': 1660950000001, 'netPercentChangeInDouble': 0.57,
        boolean_keys = ['delayed','realtimeEntitled','marginable','shortable']
        float_keys = ['52WkHigh','52WkLow','askPrice','bidPrice','closePrice','divAmount','divYield','highPrice','lastPrice','lowPrice','mark','markChangeInDouble','markPercentChangeInDouble','nAV','netChange','netPercentChangeInDouble','openPrice','peRatio','regularMarketLastPrice','regularMarketNetChange','regularMarketPercentChangeInDouble','volatility']
        int_keys = ['askSize','bidSize','digits','lastSize','quoteTimeInLong','regularMarketLastSize','regularMarketTradeTimeInLong','totalVolume','tradeTimeInLong']
        string_keys = ['askId','assetMainType','assetSubType','assetType','bidId','bidTick','cusip','description','divDate','exchange','exchangeName','lastId','securityStatus','symbol']
        quote = self.latest.quote(TEST_SYMBOL_ONE)
        print(quote)
        print(int(time.time()))
        self.assertFalse('unknown_symbols' in quote)
        symbol = TEST_SYMBOL_ONE.upper()
        self.assertTrue(symbol in quote['quotes'])
        self.assertEqual(quote['quotes'][symbol]['symbol'], symbol)
        for key in quote['quotes'][symbol]:
            self.assertTrue(key in boolean_keys or key in float_keys or key in int_keys or key in string_keys)
        for key in boolean_keys:
            self.assertTrue(isinstance(quote['quotes'][symbol][key], bool))
        for key in float_keys:
            self.assertTrue(isinstance(quote['quotes'][symbol][key], float))
        for key in int_keys:
            self.assertTrue(isinstance(quote['quotes'][symbol][key], int))
        for key in string_keys:
            self.assertTrue(isinstance(quote['quotes'][symbol][key], str))
        self.assertEqual(quote['quotes'][symbol]['assetMainType'], 'EQUITY')
        self.assertEqual(quote['quotes'][symbol]['assetType'], 'EQUITY')
        self.assertEqual(quote['quotes'][symbol]['exchange'], TEST_SYMBOL_ONE_QUOTE_EXCHANGE)
        self.assertEqual(quote['quotes'][symbol]['exchangeName'], TEST_SYMBOL_ONE_QUOTE_EXCHANGE_NAME)
        self.assertGreaterEqual(quote['quotes'][symbol]['askPrice'],quote['quotes'][symbol]['bidPrice'])
        self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['lowPrice'])
        self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['openPrice'])
        self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['closePrice'])
        self.assertLessEqual(quote['quotes'][symbol]['lowPrice'],quote['quotes'][symbol]['openPrice'])
        self.assertLessEqual(quote['quotes'][symbol]['lowPrice'],quote['quotes'][symbol]['closePrice'])
        self.assertEqual(round(quote['quotes'][symbol]['netChange'],2), round(quote['quotes'][symbol]['lastPrice'] - quote['quotes'][symbol]['closePrice'],2))
        quote = self.latest.quote([TEST_SYMBOL_ONE.lower(),TEST_SYMBOL_TWO,TEST_SYMBOL_FAKE.lower()])
        self.assertTrue(TEST_SYMBOL_FAKE.upper() in quote['unknown_symbols'])
        for symbol in [TEST_SYMBOL_ONE.upper(),TEST_SYMBOL_TWO.upper()]:
            self.assertEqual(quote['quotes'][symbol]['symbol'], symbol)
            for key in quote['quotes'][symbol]:
                self.assertTrue(key in boolean_keys or key in float_keys or key in int_keys or key in string_keys)
            for key in boolean_keys:
                self.assertTrue(isinstance(quote['quotes'][symbol][key], bool))
            for key in float_keys:
                self.assertTrue(isinstance(quote['quotes'][symbol][key], float))
            for key in int_keys:
                self.assertTrue(isinstance(quote['quotes'][symbol][key], int))
            for key in string_keys:
                self.assertTrue(isinstance(quote['quotes'][symbol][key], str))
            self.assertEqual(quote['quotes'][symbol]['assetMainType'], 'EQUITY')
            self.assertEqual(quote['quotes'][symbol]['assetType'], 'EQUITY')
            if symbol == TEST_SYMBOL_ONE.upper():
                self.assertEqual(quote['quotes'][symbol]['exchange'], TEST_SYMBOL_ONE_QUOTE_EXCHANGE)
                self.assertEqual(quote['quotes'][symbol]['exchangeName'], TEST_SYMBOL_ONE_QUOTE_EXCHANGE_NAME)
            else:
                self.assertEqual(quote['quotes'][symbol]['exchange'], TEST_SYMBOL_TWO_QUOTE_EXCHANGE)
                self.assertEqual(quote['quotes'][symbol]['exchangeName'], TEST_SYMBOL_TWO_QUOTE_EXCHANGE_NAME)
            self.assertGreaterEqual(quote['quotes'][symbol]['askPrice'],quote['quotes'][symbol]['bidPrice'])
            self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['lowPrice'])
            self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['openPrice'])
            self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['closePrice'])
            self.assertLessEqual(quote['quotes'][symbol]['lowPrice'],quote['quotes'][symbol]['openPrice'])
            self.assertLessEqual(quote['quotes'][symbol]['lowPrice'],quote['quotes'][symbol]['closePrice'])
            self.assertEqual(round(quote['quotes'][symbol]['netChange'],2), round(quote['quotes'][symbol]['lastPrice'] - quote['quotes'][symbol]['closePrice'],2))
        quote = self.latest.quote([TEST_SYMBOL_FAKE,TEST_SYMBOL_FAKE_TWO.lower()])
        self.assertFalse('quotes' in quote)
        self.assertTrue(TEST_SYMBOL_FAKE.upper() in quote['unknown_symbols'])
        self.assertTrue(TEST_SYMBOL_FAKE_TWO.upper() in quote['unknown_symbols'])

    def test_intra_day(self):
        return # ALEX
        quotes = self.intraday.quote(TEST_SYMBOL_ONE)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
