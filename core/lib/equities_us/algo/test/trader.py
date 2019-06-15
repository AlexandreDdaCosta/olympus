#!/usr/bin/env python3

import json, unittest

import olympus.equities_us.algo.trader as trader
import olympus.testing as testing

class TestTrade(testing.Test):

    def setUp(self):
        self.trade = trader.Trade()

if __name__ == '__main__':
	unittest.main()
