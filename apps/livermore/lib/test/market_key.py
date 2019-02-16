#!/usr/bin/env python3

import unittest

import olympus.testing as testing
import livermore.market_key as market_key

class TestSomething(testing.Test):

    def setUp(self):
        self.chart = market_key.Chart()
        self.backtest = market_key.Backtest()

    def test_chart(self):
        chart = self.chart.chartpoints()
        print(chart)

    def test_backtest(self):
        pass

if __name__ == '__main__':
	unittest.main()
