#!/usr/bin/env python3

import unittest

import olympus.testing as testing
import larry.market_key as market_key

class MarketKey(testing.Test):

    def setUp(self):
        pass

    def test_chart(self):
        self.calculator = market_key.Calculate()
        chart = self.calculator.chartpoints()
        print(chart)

if __name__ == '__main__':
	unittest.main()
