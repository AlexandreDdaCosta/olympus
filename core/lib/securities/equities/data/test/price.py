#!/usr/bin/env python3

# pyright: reportGeneralTypeIssues=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportOptionalSubscript=false

import re
import sys
import time
import unittest

from datetime import datetime as dt, timedelta
from dateutil import tz

import olympus.securities.equities.data.price as price
import olympus.testing as testing

from olympus import Dates
from olympus.securities.equities import (
    REGULAR_MARKET_CLOSE_TIME,
    REGULAR_MARKET_OPEN_TIME,
    SHORTENED_MARKET_CLOSE_TIME,
    TEST_SYMBOL_DIV,
    TEST_SYMBOL_DIV_QUOTE_EXCHANGE,
    TEST_SYMBOL_DIV_QUOTE_EXCHANGE_NAME,
    TEST_SYMBOL_DIVSPLIT,
    TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE,
    TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE_NAME,
    TEST_SYMBOL_FAKE,
    TEST_SYMBOL_FAKE_TWO,
    TEST_SYMBOL_NODIVSPLIT,
    TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE,
    TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE_NAME,
    TEST_SYMBOL_SPLIT
)
from olympus.securities.equities.data import Connection, TIMEZONE
from olympus.securities.equities.data.equity_datetime import OLDEST_QUOTE_DATE
from olympus.securities.equities.data.equity_datetime import TradingDates
from olympus.securities.equities.data.price import (
    VALID_DAILY_WEEKLY_PERIODS,
    VALID_MONTHLY_PERIODS
)
from olympus.securities.equities.data.symbols import SymbolNotFoundError

# Standard run parameters:
# sudo su -s /bin/bash -c '... price.py' <current user OS name>

date_utils = Dates()


class TestPrice(testing.Test):

    def __init__(self, test_case):
        super(TestPrice, self).__init__(test_case)

    def test_adjustments(self):  # noqa: C901
        if self.skip_test():
            return
        self.print_test('Adjustments to prices and volume')
        mongo_data = Connection(self.username)
        self.print('Splits.')
        adjustments = price.Adjustments(self.username)
        with self.assertRaises(SymbolNotFoundError):
            adjustments.splits(TEST_SYMBOL_FAKE)
        splits = adjustments.splits(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(splits.first())
        price_collection = 'price.' + TEST_SYMBOL_DIVSPLIT
        collection = mongo_data.db[price_collection]
        initial_split_data = collection.find_one({'Adjustment': 'Splits'},
                                                 {'_id': 0, 'Interval': 0})
        splits = adjustments.splits(TEST_SYMBOL_DIVSPLIT, regen=True)
        last_split_date = None
        entry = splits.next()
        self.print('Verifying sort of splits.')
        while entry is not None:
            if last_split_date is not None:
                self.assertLess(entry.date, last_split_date)
            last_split_date = entry.date
            entry = splits.next()
        self.print('Checking for regeneration.')
        first_regen_split_data = collection.find_one({'Adjustment': 'Splits'},
                                                     {'_id': 0, 'Interval': 0})
        if initial_split_data is not None:
            self.assertGreater(first_regen_split_data['Time'],
                               initial_split_data['Time'])
        self.print('Dividends.')
        with self.assertRaises(SymbolNotFoundError):
            dividends = adjustments.dividends(TEST_SYMBOL_FAKE)
        dividends = adjustments.dividends(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(dividends.first())
        initial_dividend_data = collection.find_one(
            {'Adjustment': 'Dividends'},
            {'_id': 0, 'Interval': 0})
        dividends = adjustments.dividends(TEST_SYMBOL_DIVSPLIT, regen=True)
        dividends.sort('date')
        last_dividend_date = None
        dividend = dividends.next()
        self.print('Verifying reverse sort of dividends.')
        while dividend is not None:
            if last_dividend_date is not None:
                self.assertGreater(dividend.date, last_dividend_date)
            last_dividend_date = dividend.date
            dividend = dividends.next()
        regen_dividend_data = collection.find_one({'Adjustment': 'Dividends'},
                                                  {'_id': 0, 'Interval': 0})
        regen_split_data = collection.find_one({'Adjustment': 'Splits'},
                                               {'_id': 0, 'Interval': 0})
        self.assertGreater(regen_split_data['Time'],
                           first_regen_split_data['Time'])
        if initial_dividend_data is not None:
            self.assertGreater(regen_dividend_data['Time'],
                               initial_dividend_data['Time'])
        self.print('Data checks.')
        with self.assertRaises(SymbolNotFoundError):
            dividends = adjustments.adjustments(TEST_SYMBOL_FAKE)
        adjustments_data = adjustments.adjustments(TEST_SYMBOL_DIVSPLIT)
        adjustments_split_data = collection.find_one({'Adjustment': 'Splits'},
                                                     {'_id': 0, 'Interval': 0})
        self.assertEqual(adjustments_split_data['Time'],
                         regen_split_data['Time'])
        self.assertTrue(adjustments_split_data['Splits'] ==
                        regen_split_data['Splits'])
        adjustments_dividend_data = collection.find_one(
            {'Adjustment': 'Dividends'},
            {'_id': 0, 'Interval': 0})
        self.assertEqual(adjustments_dividend_data['Time'],
                         regen_dividend_data['Time'])
        self.assertTrue(adjustments_dividend_data['Dividends'] ==
                        regen_dividend_data['Dividends'])
        last_adjustment_date = None
        adjustment = adjustments_data.next()
        while adjustment is not None:
            timezone_date = date_utils.utc_date_to_tz_date(adjustment.date,
                                                           TIMEZONE)
            if last_adjustment_date is not None:
                self.assertLessEqual(timezone_date, last_adjustment_date)
            last_adjustment_date = timezone_date
            if adjustment.get('dividend') is not None:
                dividend = dividends.get_by_attribute('date', timezone_date)
                self.assertEqual(timezone_date, dividend.date)
            if adjustment.get('price_adjustment') is not None:
                split = splits.get_by_attribute('date', timezone_date)
                self.assertEqual(timezone_date, split.date)
                self.assertEqual(adjustment.price_adjustment,
                                 split.price_dividend_adjustment)
                self.assertEqual(adjustment.volume_adjustment,
                                 split.volume_adjustment)
            adjustment = adjustments_data.next()
        adjustment_data = collection.find_one({'Adjustment': 'Merged'},
                                              {'_id': 0, 'Interval': 0})
        adjustments.adjustments(TEST_SYMBOL_DIVSPLIT, regen=True)
        regen_adjustment_data = collection.find_one({'Adjustment': 'Merged'},
                                                    {'_id': 0, 'Interval': 0})
        self.assertGreater(regen_adjustment_data['Time'],
                           adjustment_data['Time'])

    def test_daily(self):  # noqa: F403
        if self.skip_test():
            return
        self.print_test('Daily quotes')
        daily = price.Daily(self.username)
        mongo_data = Connection(self.username)
        quotes = daily.quote(TEST_SYMBOL_DIVSPLIT)
        price_collection = 'price.' + TEST_SYMBOL_DIVSPLIT
        collection = mongo_data.db[price_collection]
        with self.assertRaises(SymbolNotFoundError):
            quotes = daily.quote(TEST_SYMBOL_FAKE)
        quotes = daily.quote(TEST_SYMBOL_DIV, regen=True)
        self.print('Compare returned data to database.')
        quotes = daily.quote(TEST_SYMBOL_DIVSPLIT)
        first_date = quotes.first().date
        init_quote_data = collection.find_one({'Interval': '1d'},
                                              {'_id': 0,
                                               'Interval': 0,
                                               'Quotes': 0})
        quotes = daily.quote(TEST_SYMBOL_DIVSPLIT, regen=True)
        regen_quote_data = collection.find_one({'Interval': '1d'},
                                               {'_id': 0,
                                                'Interval': 0,
                                                'Quotes': 0})
        self.assertGreater(regen_quote_data['Time'], init_quote_data['Time'])
        self.print('Invalid date checks.')
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT,
                        start_date=dt(2022,
                                      2,
                                      29,
                                      0,
                                      0,
                                      0).replace(tzinfo=tz.gettz(TIMEZONE)))
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT,
                        end_date=dt(2022,
                                    2,
                                    29,
                                    0,
                                    0,
                                    0).replace(tzinfo=tz.gettz(TIMEZONE)))
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT, start_date='BADLYFORMATTEDDATE')
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT, end_date='BADLYFORMATTEDDATE')
        tomorrow = ((dt.now().astimezone() + timedelta(days=1))
                    .replace(tzinfo=tz.gettz(TIMEZONE)))
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT, start_date=tomorrow)
        a_while_ago = ((dt.now().astimezone() - timedelta(days=90))
                       .replace(tzinfo=tz.gettz(TIMEZONE)))
        today = dt.now().astimezone().replace(tzinfo=tz.gettz(TIMEZONE))
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT,
                        start_date=today,
                        end_date=a_while_ago)
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT, period='BADPERIOD')
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT,
                        period='1Y',
                        start_date=a_while_ago)
        with self.assertRaises(Exception):
            daily.quote(TEST_SYMBOL_DIVSPLIT,
                        period='1Y',
                        end_date=a_while_ago)
        quotes = daily.quote(TEST_SYMBOL_DIVSPLIT,
                             start_date=a_while_ago,
                             end_date=today)
        curr_range_date = None
        quote = quotes.next()
        self.print('Verification of valid quote.')
        while quote is not None:
            if curr_range_date is None:
                self.assertGreaterEqual(quote.date, a_while_ago)
            if quote.adjusted_close is not None:
                self.assertLess(quote.adjusted_close, quote.close)
            if quote.adjusted_low is not None:
                self.assertLess(quote.adjusted_low, quote.low)
            if quote.adjusted_high is not None:
                self.assertLess(quote.adjusted_high, quote.high)
            if quote.adjusted_open is not None:
                self.assertLess(quote.adjusted_open, quote.open)
            if quote.adjusted_volume is not None:
                self.assertGreaterEqual(quote.adjusted_volume, quote.volume)
            self.assertGreaterEqual(quote.high, quote.close)
            self.assertGreater(quote.high, quote.low)
            self.assertGreaterEqual(quote.high, quote.open)
            self.assertLessEqual(quote.low, quote.close)
            self.assertLessEqual(quote.low, quote.open)
            curr_range_date = quote.date
            quote = quotes.next()
        self.assertLessEqual(curr_range_date, today)
        self.print('Check range of raturned dates for all valid periods.')
        for period in VALID_DAILY_WEEKLY_PERIODS.keys():
            quotes = daily.quote(TEST_SYMBOL_DIVSPLIT, period=period)
            first_period_date = quotes.first().date
            if period == 'All':
                self.assertEqual(first_date, first_period_date)
            else:
                # Add 4 in case of mid-week day adjustment
                past_days = VALID_DAILY_WEEKLY_PERIODS[period] + 4
                now = dt.now().astimezone()
                max_past_date = ((dt(now.year, now.month, now.day, 0, 0, 0) -
                                 timedelta(days=past_days))
                                 .replace(tzinfo=tz.gettz(TIMEZONE)))
                self.assertLessEqual(max_past_date, first_period_date)
        self.print('Remove the last price record by date, then get the ' +
                   'quote again. Check that the record was restored.')
        quotes = daily.quote(TEST_SYMBOL_DIVSPLIT, regen=True)
        interval_data = collection.find_one({'Interval': '1d'},
                                            {'_id': 0, 'Interval': 0})
        last_date = None
        previous_date = None
        for quote_date in sorted(interval_data['Quotes'],
                                 key=lambda k: k[0],
                                 reverse=True):
            if last_date is None:
                last_date = date_utils.utc_date_to_tz_date(quote_date[0],
                                                           TIMEZONE)
                continue
            if previous_date is None:
                previous_date = date_utils.utc_date_to_tz_date(quote_date[0],
                                                               TIMEZONE)
                break
        if previous_date is not None:
            self.print('Test for regeneration of missing dates by ' +
                       'simulating the result from one trading day ' +
                       'previous after doing full regeneration.')
            time_object = dt(previous_date.year,
                             previous_date.month,
                             previous_date.day,
                             23,
                             0,
                             0).replace(tzinfo=tz.gettz())
            collection.update_one({'Interval': '1d',
                                   'Quotes': {'$elemMatch':
                                              {'0': {'$eq': last_date}}}},
                                  {'$unset': {"Quotes.$": 1}})
            collection.update_one({'Interval': '1d'},
                                  {'$pull': {'Quotes': None}})
            collection.update_one({'Interval': '1d'},
                                  {"$set": {'End Date': previous_date,
                                            'Time': time_object}})
            data = collection.find_one({'Interval': '1d'},
                                       {'Quotes': {'$elemMatch':
                                                   {'0': {'$eq': last_date}}}})
            self.assertFalse('Quotes' in data)
            data = collection.find_one({'Interval': '1d'},
                                       {'Quotes':
                                        {'$elemMatch':
                                         {'0': {'$eq': previous_date}}}})
            self.assertTrue('Quotes' in data)
            quotes = daily.quote(TEST_SYMBOL_DIVSPLIT)
            data = collection.find_one({'Interval': '1d'},
                                       {'Quotes': {'$elemMatch':
                                                   {'0': {'$eq': last_date}}}})
            self.assertTrue('Quotes' in data)

    def test_weekly(self):
        if self.skip_test():
            return
        self.print_test('Weekly quotes')
        weekly = price.Weekly(self.username)
        with self.assertRaises(SymbolNotFoundError):
            quotes = weekly.quote(TEST_SYMBOL_FAKE)
        now = dt.now().astimezone()
        quotes = weekly.quote(TEST_SYMBOL_DIVSPLIT, period='All')
        first_date = quotes.first().date
        quote = quotes.next()
        self.print('Verify returned data for a valid weekly quote request.')
        while quote is not None:
            if quote.adjusted_close is not None:
                self.assertLessEqual(quote.adjusted_close, quote.close)
            if quote.adjusted_low is not None:
                self.assertLessEqual(quote.adjusted_low, quote.low)
            if quote.adjusted_high is not None:
                self.assertLessEqual(quote.adjusted_high, quote.high)
            if quote.adjusted_open is not None:
                self.assertLessEqual(quote.adjusted_open, quote.open)
            if quote.adjusted_volume is not None:
                self.assertGreaterEqual(quote.adjusted_volume, quote.volume)
            self.assertGreaterEqual(quote.high, quote.close)
            self.assertGreaterEqual(quote.high, quote.low)
            self.assertGreaterEqual(quote.high, quote.open)
            self.assertLessEqual(quote.low, quote.close)
            self.assertLessEqual(quote.low, quote.open)
            quote = quotes.next()
        self.print('Verify returned date ranges for all valid periods.')
        for period in VALID_DAILY_WEEKLY_PERIODS.keys():
            if period == 'All':
                continue
            # Add 4 in case of weekday adjustment
            past_days = VALID_DAILY_WEEKLY_PERIODS[period] + 4
            max_past_date = ((dt(now.year, now.month, now.day, 0, 0, 0) -
                             timedelta(days=past_days))
                             .replace(tzinfo=tz.gettz(TIMEZONE)))
            quotes = weekly.quote(TEST_SYMBOL_DIV, period=period)
            first_period_date = quotes.first().date
            self.assertLessEqual(first_date, first_period_date)
            self.assertLessEqual(max_past_date, first_period_date)

    def test_monthly(self):
        if self.skip_test():
            return
        self.print_test('Monthly quotes')
        monthly = price.Monthly(self.username)
        with self.assertRaises(SymbolNotFoundError):
            quotes = monthly.quote(TEST_SYMBOL_FAKE)
        quotes = monthly.quote(TEST_SYMBOL_DIVSPLIT, period='All')
        first_date = quotes.first().date
        quote = quotes.next()
        self.print('Verify returned data for a valid monthly quote request.')
        while quote is not None:
            if quote.adjusted_close is not None:
                self.assertLessEqual(quote.adjusted_close, quote.close)
            if quote.adjusted_low is not None:
                self.assertLessEqual(quote.adjusted_low, quote.low)
            if quote.adjusted_high is not None:
                self.assertLessEqual(quote.adjusted_high, quote.high)
            if quote.adjusted_open is not None:
                self.assertLessEqual(quote.adjusted_open, quote.open)
            if quote.adjusted_volume is not None:
                self.assertGreaterEqual(quote.adjusted_volume, quote.volume)
            self.assertGreaterEqual(quote.high, quote.close)
            self.assertGreaterEqual(quote.high, quote.low)
            self.assertGreaterEqual(quote.high, quote.open)
            self.assertLessEqual(quote.low, quote.close)
            self.assertLessEqual(quote.low, quote.open)
            quote = quotes.next()
        self.print('Verify returned date ranges for all valid periods.')
        for period in VALID_MONTHLY_PERIODS:
            if period == 'All':
                continue
            past_period = int(re.sub(r"[Y]", "", period))
            now = dt.now().astimezone()
            max_past_date = dt(now.year - int(past_period),
                               now.month,
                               1,
                               0,
                               0,
                               0).replace(tzinfo=tz.gettz(TIMEZONE))
            quotes = monthly.quote(TEST_SYMBOL_DIVSPLIT, period)
            first_period_date = quotes.first().date
            self.assertLessEqual(first_date, first_period_date)
            self.assertLessEqual(max_past_date, first_period_date)

    def test_latest(self):
        if self.skip_test():
            return
        self.print_test('Latest quotes')
        latest = price.Latest(self.username)
        result = latest.quote(TEST_SYMBOL_DIV.lower())
        symbol = TEST_SYMBOL_DIV.upper()
        self.print('Verify returned data format and contents.')
        self.assertIsNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        quote = result.get_symbol(TEST_SYMBOL_DIV)
        quoteTimeLong = int(time.time() * 1000)
        self.assertEqual(quote.symbol, symbol)
        self.assertEqual(quote.exchange,
                         TEST_SYMBOL_DIV_QUOTE_EXCHANGE)
        self.assertEqual(quote.exchange_name,
                         TEST_SYMBOL_DIV_QUOTE_EXCHANGE_NAME)
        self.assertGreaterEqual(quote.ask, quote.bid)
        self.assertGreaterEqual(quote.high, quote.low)
        self.assertGreaterEqual(quote.high, quote.open)
        self.assertLessEqual(quote.low, quote.open)
        self.assertGreaterEqual(quoteTimeLong, quote.quote_time_in_long)
        self.assertGreaterEqual(quoteTimeLong, quote.trade_time_in_long)
        self.assertGreaterEqual(quoteTimeLong,
                                quote.regular_market_trade_time_in_long)
        self.assertGreaterEqual(quote.trade_time_in_long,
                                quote.regular_market_trade_time_in_long)
        self.assertLessEqual(abs(round(quote.net_change -
                                       (quote.last_price - quote.close), 2)),
                             .01)
        self.print('Mixed request including (1) Valid symbol, ' +
                   '(2) Valid but incorrectly cased symbol, and ' +
                   '(3) Unknown symbol.')
        result = latest.quote([TEST_SYMBOL_NODIVSPLIT.lower(),
                               TEST_SYMBOL_DIVSPLIT,
                               TEST_SYMBOL_FAKE.lower()])
        quoteTimeLong = int(time.time() * 1000)
        self.assertIsNotNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        self.assertEqual(len(result.unknown_symbols), 1)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        for symbol in [TEST_SYMBOL_NODIVSPLIT, TEST_SYMBOL_DIVSPLIT]:
            quote = result.get_symbol(symbol)
            self.assertEqual(quote.symbol, symbol)
            if symbol == TEST_SYMBOL_NODIVSPLIT:
                self.assertEqual(quote.exchange,
                                 TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE)
                self.assertEqual(quote.exchange_name,
                                 TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE_NAME)
            else:
                self.assertEqual(quote.exchange,
                                 TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE)
                self.assertEqual(quote.exchange_name,
                                 TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE_NAME)
            self.assertGreaterEqual(quote.ask, quote.bid)
            self.assertGreaterEqual(quote.high, quote.low)
            self.assertGreaterEqual(quote.high, quote.open)
            self.assertLessEqual(quote.low, quote.open)
            self.assertGreaterEqual(quoteTimeLong, quote.quote_time_in_long)
            self.assertGreaterEqual(quoteTimeLong, quote.trade_time_in_long)
            self.assertGreaterEqual(quoteTimeLong,
                                    quote.regular_market_trade_time_in_long)
            self.assertGreaterEqual(quote.trade_time_in_long,
                                    quote.regular_market_trade_time_in_long)
            self.assertLessEqual(abs(round(quote.net_change -
                                           (quote.last_price - quote.close),
                                           2)),
                                 .01)
        self.print('Request including only unknown symbols.')
        result = latest.quote([TEST_SYMBOL_FAKE, TEST_SYMBOL_FAKE_TWO.lower()])
        self.assertIsNone(result.get_quotes())
        self.assertIsNotNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        self.assertEqual(len(result.unknown_symbols), 2)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE_TWO in result.unknown_symbols)

    def test_intraday(self):  # noqa: F403
        if self.skip_test():
            return
        self.print_test('Intraday quotes')
        intraday = price.Intraday(self.username)
        trading_dates = TradingDates()
        with self.assertRaises(SymbolNotFoundError):
            intraday.quote(TEST_SYMBOL_FAKE)
        self.print('Check for valid frequencies and periods.')
        bad_min_frequency = min(intraday.VALID_INTRADAY_FREQUENCIES.keys()) - 1
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_DIV, frequency=bad_min_frequency)
        bad_max_frequency = max(intraday.VALID_INTRADAY_FREQUENCIES.keys()) + 1
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_DIV, frequency=bad_max_frequency)
        bad_min_period = min(intraday.VALID_INTRADAY_PERIODS) - 1
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_DIV, period=bad_min_period)
        bad_max_period = max(intraday.VALID_INTRADAY_PERIODS) + 1
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_DIV, period=bad_max_period)
        for frequency in intraday.VALID_INTRADAY_FREQUENCIES:
            intraday.valid_frequency(frequency)
        for period in intraday.VALID_INTRADAY_PERIODS:
            intraday.valid_period(period)
        period = intraday.valid_period()  # Period can be none
        self.assertEqual(period, intraday.DEFAULT_INTRADAY_PERIOD)
        self.print('The next two series use the default values ' +
                   'for period and frequency.')
        quotes = intraday.quote(TEST_SYMBOL_DIV)
        quote = quotes.next(return_raw_data=True)
        last_quote_time = None
        while quote is not None:
            if (last_quote_time is not None and
                    quote['Date'].day == last_quote_time.day):
                # Extended hours quotes occasonally skip intervals,
                # presumably because of a lack of trading activity
                if (last_quote_time.hour >= 9 and
                        last_quote_time.minute >= 30 and
                        last_quote_time.hour < 16):
                    self.assertEqual(intraday.DEFAULT_INTRADAY_FREQUENCY,
                                     int((quote['Date'] - last_quote_time)
                                         .total_seconds() / 60))
            last_quote_time = quote['Date']
            quote = quotes.next(return_raw_data=True)
        quotes = intraday.quote(TEST_SYMBOL_DIV,
                                need_extended_hours_data=False)
        quote = quotes.next()
        last_quote_time = None
        half_days = None
        while quote is not None:
            if last_quote_time is None:
                half_days = trading_dates.half_days(quote.date)
            if (last_quote_time is None or
                    quote.date.day > last_quote_time.day or
                    quote.date.month > last_quote_time.month):
                self.assertEqual(REGULAR_MARKET_OPEN_TIME,
                                 quote.date.strftime("%H:%M:%S"))
            if (last_quote_time is not None and
                    (quote.date.day > last_quote_time.day or
                     quote.date.month > last_quote_time.month)):
                yesterday_close_time_string = ((
                    last_quote_time +
                    timedelta(minutes=intraday.DEFAULT_INTRADAY_FREQUENCY))
                    .strftime("%H:%M:%S"))
                midnight_quote_date = dt(quote.date.year,
                                         quote.date.month,
                                         quote.date.day,
                                         0,
                                         0,
                                         0).replace(tzinfo=tz.gettz(TIMEZONE))
                if half_days is None or midnight_quote_date not in half_days:
                    self.assertEqual(REGULAR_MARKET_CLOSE_TIME,
                                     yesterday_close_time_string)
                else:
                    self.assertEqual(SHORTENED_MARKET_CLOSE_TIME,
                                     yesterday_close_time_string)
            last_quote_time = quote.date
            quote = quotes.next()
        today = dt.now().astimezone()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        self.print('Check all period/frequency combinations.')
        for period in intraday.VALID_INTRADAY_PERIODS:
            with self.assertRaises(Exception):
                # Cannot specify period and start_date together
                intraday.quote(TEST_SYMBOL_DIVSPLIT,
                               period=period,
                               start_date=two_days_ago)
            for frequency in intraday.VALID_INTRADAY_FREQUENCIES:
                # If we have an end date, the number of available periods will
                # be limited based on the frequency of data requested.
                # Here we generate this error (or another date error)
                oldest_available_date = \
                    intraday.oldest_available_date(frequency)
                error_date = oldest_available_date + timedelta(days=period - 2)
                with self.assertRaises(Exception):
                    intraday.quote(TEST_SYMBOL_NODIVSPLIT,
                                   need_extended_hours_data=False,
                                   period=period,
                                   frequency=frequency,
                                   end_date=error_date)
                # The next series is limited to regular trading hours to
                # ensure there are no time periods with no data
                quotes = intraday.quote(TEST_SYMBOL_DIVSPLIT,
                                        period=period,
                                        frequency=frequency,
                                        need_extended_hours_data=False)
                last_quote_time = None
                quote = quotes.next()
                while quote is not None:
                    if (last_quote_time is not None and
                            quote.date.year == last_quote_time.year and
                            quote.date.month == last_quote_time.month and
                            quote.date.day == last_quote_time.day):
                        self.assertEqual(frequency,
                                         int((quote.date - last_quote_time)
                                             .total_seconds() / 60))
                    last_quote_time = quote.date
                    quote = quotes.next()
        self.print('Checks for bad absolute and relative dates.')
        too_old_date = OLDEST_QUOTE_DATE - timedelta(days=1)
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_SPLIT, start_date=too_old_date)
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_SPLIT, end_date=too_old_date)
        tomorrow = dt.now().astimezone() + timedelta(days=1)
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_SPLIT, start_date=tomorrow)
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_SPLIT, end_date=tomorrow)
        with self.assertRaises(Exception):
            intraday.quote(TEST_SYMBOL_SPLIT,
                           end_date=two_days_ago,
                           start_date=yesterday)
        self.print('Checks for dates that are too early when combined with' +
                   ' a frequency and for proper date ranges.')
        for frequency in intraday.VALID_INTRADAY_FREQUENCIES:
            earliest_available_date = intraday.oldest_available_date(frequency)
            too_early = earliest_available_date - timedelta(days=1)
            day_delta = round((dt.now().astimezone() -
                               dt(earliest_available_date.year,
                                  earliest_available_date.month,
                                  earliest_available_date.day)
                               .replace(tzinfo=tz.gettz())).days / 2)
            half_way_end_date = (dt.now().astimezone() -
                                 timedelta(days=day_delta))
            with self.assertRaises(Exception):
                intraday.quote(TEST_SYMBOL_SPLIT,
                               frequency=frequency,
                               start_date=too_early)
            with self.assertRaises(Exception):
                intraday.quote(TEST_SYMBOL_SPLIT,
                               frequency=frequency,
                               end_date=too_early)
            quotes = intraday.quote(TEST_SYMBOL_SPLIT,
                                    frequency=frequency,
                                    start_date=earliest_available_date)
            first_quote = quotes.first()
            last_quote = quotes.last()
            self.assertGreaterEqual(first_quote.date, earliest_available_date)
            self.assertGreaterEqual(today, last_quote.date)
            quotes = intraday.quote(TEST_SYMBOL_SPLIT,
                                    frequency=frequency,
                                    end_date=half_way_end_date)
            last_quote = quotes.last()
            # We convert these dates to midnight because the API will return
            # a full day's price date regardless of the exact time of day
            # requested as an end date
            midnight_half_way_end_date = dt(half_way_end_date.year,
                                            half_way_end_date.month,
                                            half_way_end_date.day,
                                            0,
                                            0,
                                            0).replace(tzinfo=tz.gettz())
            midnight_last_quote_date = dt(last_quote.date.year,
                                          last_quote.date.month,
                                          last_quote.date.day,
                                          0,
                                          0,
                                          0).replace(tzinfo=tz.gettz())
            self.assertGreaterEqual(midnight_half_way_end_date,
                                    midnight_last_quote_date)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        unittest.main(argv=['username'])
    else:
        unittest.main()
