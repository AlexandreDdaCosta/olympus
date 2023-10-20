#!/usr/bin/env python3

# pyright: reportGeneralTypeIssues=false
# pyright: reportOptionalMemberAccess=false

import sys
import unittest

import olympus.securities.equities.data.price as equity_price
import olympus.securities.indicators as indicators
import olympus.testing as testing

from olympus.securities.equities import TEST_SYMBOLS
from olympus.securities.indicators import (
    DEFAULT_ATR_PERIODS,
    DEFAULT_MOVING_AVERAGE_PERIODS,
    VALID_MOVING_AVERAGE_TYPES
)

# Standard run parameters:
# sudo su -s /bin/bash -c '... indicators.py' <desired run user ID>


class TestIndicators(testing.Test):

    parse_args = []
    parse_args.append(
        ('-p',
         '--period',
         {
             'action': 'store',
             'choices': ['all', 'intraday', 'daily'],
             'default': 'all',
             'help': 'Conduct tests for only indicated time period.'
         }
         ))
    parse_args.append(
        ('-s',
         '--symbol',
         {
             'action': 'store',
             'default': None,
             'help': 'Conduct tests for only indicated symbol.'
         }
         ))

    @classmethod
    def setUpClass(cls):
        TestIndicators.parser_args += TestIndicators.parse_args
        super(TestIndicators, cls).setUpClass()

    def __init__(self, test_case):
        super(TestIndicators, self).__init__(test_case)

    def test_atr(self):
        if self.skip_test():
            return
        self.print_test('Calculating average true ranges')
        if self.arguments.symbol is None:
            symbol_list = TEST_SYMBOLS
        else:
            symbol_list = []
            symbol_list.append(self.arguments.symbol.upper())
        for test_symbol in symbol_list:
            if self.arguments.period == 'all':
                test_periods = ['Daily', 'Intraday']
            else:
                test_periods = []
                test_periods.append(self.arguments.period.capitalize())
            for test_period in test_periods:
                self.print_test("%s ATR for test symbol %s"
                                % (test_period, test_symbol))
                if test_period == 'Daily':
                    price = equity_price.Daily(self.username)
                else:  # Intraday
                    price = equity_price.Intraday(self.username)
                quotes = price.quote(test_symbol)
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

    def test_moving_average(self):  # noqa: C901
        if self.skip_test():
            return
        self.print_test('Calculating moving averages')
        if self.arguments.symbol is None:
            symbol_list = TEST_SYMBOLS
        else:
            symbol_list = []
            symbol_list.append(self.arguments.symbol.upper())
        for test_symbol in symbol_list:
            if self.arguments.period == 'all':
                test_periods = ['Daily', 'Intraday']
            else:
                test_periods = []
                test_periods.append(self.arguments.period.capitalize())
            for test_period in test_periods:
                if test_period == 'Daily':
                    price = equity_price.Daily(self.username)
                else:  # Intraday
                    price = equity_price.Intraday(self.username)
                quotes = price.quote(test_symbol)
                with self.assertRaises(Exception):
                    indicators.MovingAverage(
                        quotes,
                        average_type='Foobar',
                        periods=DEFAULT_MOVING_AVERAGE_PERIODS)
                if test_period == 'Daily':
                    price = equity_price.Daily(self.username)
                else:  # intraday
                    price = equity_price.Intraday(self.username)
                quotes = price.quote(test_symbol)
                for average_type in VALID_MOVING_AVERAGE_TYPES:
                    self.print_test(
                        "%s %s moving average for test symbol "
                        "%s, %d period" %
                        (average_type,
                         test_period,
                         test_symbol,
                         DEFAULT_MOVING_AVERAGE_PERIODS))
                    with self.assertRaises(Exception):
                        indicators.MovingAverage(
                            quotes,
                            average_type=average_type,
                            periods=0)
                    with self.assertRaises(Exception):
                        indicators.MovingAverage(
                            quotes,
                            average_type=average_type,
                            periods=1000000)
                    with self.assertRaises(Exception):
                        indicators.MovingAverage(
                            quotes,
                            average_type=average_type,
                            periods='foobar')
                    ma_series = indicators.MovingAverage(
                        quotes,
                        average_type=average_type,
                        periods=DEFAULT_MOVING_AVERAGE_PERIODS)
                    self.assertEqual(quotes.count(), ma_series.count())
                    ma_entry = ma_series.next()
                    quote = quotes.next(reset=True)
                    while ma_entry is not None:
                        for known_attribute in [
                                'moving_average',
                                'moving_average_adjusted']:
                            self.assertTrue(known_attribute in
                                            ma_entry.__dict__)
                            self.assertIsNotNone(getattr(
                                ma_entry,
                                known_attribute))
                        self.assertEqual(str(ma_entry.date), str(quote.date))
                        ma_entry = ma_series.next()
                        quote = quotes.next()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        unittest.main(argv=['username'])
    else:
        unittest.main()
