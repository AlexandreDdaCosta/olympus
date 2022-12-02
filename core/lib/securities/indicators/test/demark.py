#!/usr/bin/env python3

import json
import sys
import unittest

import olympus.securities.equities.data.price as equity_price
import olympus.securities.indicators.demark as demark
import olympus.testing as testing

from olympus import USER
from olympus.securities.equities import *
from olympus.securities.indicators.demark import *

# Standard run parameters:
# sudo su -s /bin/bash -c '... indicators.py' <desired run user ID>


class TestIndicators(testing.Test):

    def __init__(self, test_case):
        super(TestIndicators, self).__init__(test_case)

    def test_sequential(self):
        if self.skip_test():
            return
        self.print_test('Calculating TD Sequential')
        # for test_symbol in [TEST_SYMBOL_DIVSPLIT,
        #                    TEST_SYMBOL_DIV,
        #                    TEST_SYMBOL_SPLIT,
        #                    TEST_SYMBOL_NODIVSPLIT]:
        for test_symbol in [TEST_SYMBOL_NODIVSPLIT]:
            # for test_period in ['Daily', 'Intraday']:
            for test_period in ['Daily']:
                self.print_test("%s TD Sequential for test symbol %s"
                                % (test_period, test_symbol))
                if test_period == 'Daily':
                    price = equity_price.Daily(self.username)
                else:  # Intraday
                    price = equity_price.Intraday(self.username)
                quotes = price.quote(test_symbol)
                '''
                with self.assertRaises(Exception):
                    indicators.AverageTrueRange(quotes, periods=0)
                with self.assertRaises(Exception):
                    indicators.AverageTrueRange(quotes, periods=1000000)
                with self.assertRaises(Exception):
                    indicators.AverageTrueRange(quotes, periods='foobar')
                atr_series = indicators.AverageTrueRange(
                        quotes,
                        periods=DEFAULT_ATR_PERIODS)
                self.assertEqual(quotes.count(), atr_series.count())
                atr_entry = atr_series.next()
                quote = quotes.next(reset=True)
                while atr_entry is not None:
                    for known_attribute in [
                            'atr',
                            'atr_adjusted',
                            'date',
                            'true_range',
                            'true_range_adjusted']:
                        self.assertTrue(known_attribute in atr_entry.__dict__)
                        self.assertIsNotNone(getattr(atr_entry,
                                                     known_attribute))
                    self.assertEqual(str(atr_entry.date), str(quote.date))
                    atr_entry = atr_series.next()
                    quote = quotes.next()
                '''


if __name__ == '__main__':
    if len(sys.argv) > 1:
        unittest.main(argv=['username'])
    else:
        unittest.main()
