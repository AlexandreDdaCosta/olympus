#!/usr/bin/env python3

import json, sys, unittest

import olympus.securities.equities.data.price as equity_price
import olympus.securities.indicators as indicators
import olympus.testing as testing

from olympus import USER
from olympus.securities.equities import *
from olympus.securities.indicators import *

# Standard run parameters:
# sudo su -s /bin/bash -c '... indicators.py' <current user OS name>

class TestIndicators(testing.Test):

    def __init__(self,test_case):
        super(TestIndicators,self).__init__(test_case)

    def test_atr(self):
        if self.skip_test('atr'):
            return
        self.print_test('Calculating average true ranges')
        self.print_test('Daily ATR for test symbol ' + TEST_SYMBOL_NODIVSPLIT)
        daily = equity_price.Daily(self.username)
        quotes = daily.quote(TEST_SYMBOL_NODIVSPLIT)
        with self.assertRaises(Exception):
            atr_series = indicators.AverageTrueRange(quotes,periods=0)
        with self.assertRaises(Exception):
            atr_series = indicators.AverageTrueRange(quotes,periods=1000000)
        atr_series = indicators.AverageTrueRange(quotes,periods=DEFAULT_ATR_PERIODS)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        unittest.main(argv=['username'])
    else:
        unittest.main()
