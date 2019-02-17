#!/usr/bin/env python3

import unittest

import olympus.testing as testing
import larry.market_key as market_key

class TestSomething(testing.Test):

    def setUp(self):
        self.chart = market_key.Chart()
        self.simulator = market_key.Simulator()

    def test_chart(self):
        chart = self.chart.chartpoints()
        print(chart)

    def test_simulator(self):
        simulation = self.simulator.backtest()
        pass

if __name__ == '__main__':
	unittest.main()
