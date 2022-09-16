#!/usr/bin/env python3

import json, sys, unittest

import olympus.securities.equities.data.price as equity_pricing
import olympus.securities.indicators as indicators
import olympus.testing as testing

from olympus import USER
from olympus.securities.equities import *
from olympus.securities.indicators import DEFAULT_ATR_LENGTH, DEFAULT_MOVING_AVERAGE_TYPE, VALID_MOVING_AVERAGE_TYPES

# Standard run parameters:
# sudo su -s /bin/bash -c '... indicators.py' USER
# Optionally:
# '... indicators.py <current_run_username>'

class TestEquityIndicators(testing.Test):

    def setUp(self):
        if len(sys.argv) == 2:
            username = self.validRunUser(sys.argv[1])
        else:
            username = self.validRunUser(USER)
        self.daily = equity_pricing.Daily(username)
        self.indicators = indicators.Indicators()

    def test_atr(self):
        daily_series = self.daily.quote(TEST_SYMBOL_NODIVSPLIT)
        atr = self.indicators.average_true_range(daily_series)
        print(json.dumps(atr,indent=4))

    def test_moving_average(self):
        daily_series = self.daily.quote(TEST_SYMBOL_NODIVSPLIT)
        ma = self.indicators.moving_average(daily_series)
        print(json.dumps(ma,indent=4))

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
