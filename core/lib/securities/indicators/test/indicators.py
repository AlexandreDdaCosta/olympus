#!/usr/bin/env python3

import json, sys, unittest

import olympus.securities.equities.data.price as equity_price
import olympus.securities.indicators as indicators
import olympus.testing as testing

from olympus import USER
from olympus.securities.equities import *
from olympus.securities.indicators import *

# Standard run parameters:
# sudo su -s /bin/bash -c '... indicators.py' <desired run user ID>

class TestIndicators(testing.Test):

    def __init__(self,test_case):
        super(TestIndicators,self).__init__(test_case)

    def test_atr(self):
        if self.skip_test():
            return
        self.print_test('Calculating average true ranges')
        for test_symbol in [TEST_SYMBOL_DIVSPLIT,TEST_SYMBOL_DIV,TEST_SYMBOL_SPLIT,TEST_SYMBOL_NODIVSPLIT]:
            for test_period in ['Daily','Intraday']:
                self.print_test("%s ATR for test symbol %s" % (test_period,test_symbol))
                if test_period == 'Daily':
                    price = equity_price.Daily(self.username)
                else: # Intraday
                    price = equity_price.Intraday(self.username)
                quotes = price.quote(test_symbol)
                with self.assertRaises(Exception):
                    indicators.AverageTrueRange(quotes,periods=0)
                with self.assertRaises(Exception):
                    indicators.AverageTrueRange(quotes,periods=1000000)
                with self.assertRaises(Exception):
                    indicators.AverageTrueRange(quotes,periods='foobar')
                atr_series = indicators.AverageTrueRange(quotes,periods=DEFAULT_ATR_PERIODS)
                self.assertEqual(quotes.count(),atr_series.count())
                atr_entry = atr_series.next()
                quote = quotes.next(reset=True)
                while atr_entry is not None:
                    for known_attribute in ['atr','atr_adjusted','date','true_range','true_range_adjusted']:
                        self.assertTrue(known_attribute in atr_entry.__dict__)
                        self.assertIsNotNone(getattr(atr_entry,known_attribute))
                    self.assertEqual(str(atr_entry.date),str(quote.date))
                    atr_entry = atr_series.next()
                    quote = quotes.next()

    def test_moving_average(self):
        if self.skip_test():
            return
        self.print_test('Calculating moving averages')
        for test_symbol in [TEST_SYMBOL_DIVSPLIT,TEST_SYMBOL_DIV,TEST_SYMBOL_SPLIT,TEST_SYMBOL_NODIVSPLIT]:
            for test_period in ['daily','intraday']:
                with self.assertRaises(Exception):
                    indicators.MovingAverage(quotes,average_type='Foobar',periods=DEFAULT_MOVING_AVERAGE_PERIODS)
                if test_period == 'daily':
                    price = equity_price.Daily(self.username)
                else: # intraday
                    price = equity_price.Intraday(self.username)
                quotes = price.quote(test_symbol)
                for average_type in VALID_MOVING_AVERAGE_TYPES:
                    self.print_test("%s %s moving average for test symbol %s, %d period" % (average_type,test_period,test_symbol,DEFAULT_MOVING_AVERAGE_PERIODS))
                    with self.assertRaises(Exception):
                        indicators.MovingAverage(quotes,average_type=average_type,periods=0)
                    with self.assertRaises(Exception):
                        indicators.MovingAverage(quotes,average_type=average_type,periods=1000000)
                    with self.assertRaises(Exception):
                        indicators.MovingAverage(quotes,average_type=average_type,periods='foobar')
                    ma_series = indicators.MovingAverage(quotes,average_type=average_type,periods=DEFAULT_MOVING_AVERAGE_PERIODS)
                    self.assertEqual(quotes.count(),ma_series.count())
                    ma_entry = ma_series.next()
                    quote = quotes.next(reset=True)
                    while ma_entry is not None:
                        for known_attribute in ['moving_average','moving_average_adjusted']:
                            self.assertTrue(known_attribute in ma_entry.__dict__)
                            self.assertIsNotNone(getattr(ma_entry,known_attribute))
                        self.assertEqual(str(ma_entry.date),str(quote.date))
                        ma_entry = ma_series.next()
                        quote = quotes.next()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        unittest.main(argv=['username'])
    else:
        unittest.main()
