#!/usr/bin/env python3

import sys
import unittest

import olympus.securities.equities.data.price as equity_price
import olympus.securities.indicators.demark.algo.sequential as sequential
import olympus.testing as testing

from olympus.securities.equities import (
    TEST_SYMBOLS
)

# Standard run parameters:
# sudo su -s /bin/bash -c '... demark.py' <desired run user ID>


class TestDemark(testing.Test):

    def __init__(self, test_case):
        parser_args = []
        parser_args.append(
            ('-p',
             '--period',
             {
                 'action': 'store',
                 'choices': ['all', 'intraday', 'daily'],
                 'default': 'all',
                 'help': 'Conduct tests for only indicated time period.'
             }
             ))
        parser_args.append(
            ('-s',
             '--symbol',
             {
                 'action': 'store',
                 'default': None,
                 'help': 'Conduct tests for only indicated symbol.'
             }
             ))
        super(TestDemark, self).__init__(
            test_case,
            parser_args=parser_args)

    def test_sequential(self):
        if self.skip_test():
            return
        self.print_test('Calculating TD Sequential')
        if self.args.symbol is None:
            symbol_list = TEST_SYMBOLS
        else:
            symbol_list = []
            symbol_list.append(self.args.symbol.upper())
        for test_symbol in symbol_list:
            if self.args.period == 'all':
                test_periods = ['Daily', 'Intraday']
            else:
                test_periods = []
                test_periods.append(self.args.period.capitalize())
            for test_period in test_periods:
                self.print_test("%s TD Sequential for test symbol %s"
                                % (test_period, test_symbol))
                if test_period == 'Daily':
                    price = equity_price.Daily(self.username)
                else:  # Intraday
                    price = equity_price.Intraday(self.username)
                quotes = price.quote(test_symbol, preformat=True)
                with self.assertRaises(Exception):
                    sequential.Sequential(quotes, array_periods=0)
                with self.assertRaises(Exception):
                    sequential.Sequential(quotes, array_periods=1000000)
                with self.assertRaises(Exception):
                    sequential.Sequential(quotes, array_periods='foobar')
                with self.assertRaises(Exception):
                    sequential.Sequential(quotes, formation_periods=0)
                with self.assertRaises(Exception):
                    sequential.Sequential(quotes, formation_periods=1000000)
                with self.assertRaises(Exception):
                    sequential.Sequential(quotes, formation_periods='foobar')
                obj = sequential.Sequential(
                    quotes,
                    array_periods=sequential.DEFAULT_ARRAY_PERIODS,
                    formation_periods=sequential.DEFAULT_FORMATION_PERIODS)
                print(obj)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        unittest.main(argv=['username'])
    else:
        unittest.main()
