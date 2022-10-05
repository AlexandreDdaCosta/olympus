#!/usr/bin/env python3

import json, jsonschema, os, re, sys, time, unittest

from datetime import date, datetime as dt, timedelta, timezone
from dateutil import tz
from jsonschema import validate

import olympus.securities.equities.data as data
import olympus.securities.equities.data.price as price
import olympus.testing as testing

from olympus import Dates, String, USER
from olympus.securities.equities import *
from olympus.securities.equities.data import TIMEZONE
from olympus.securities.equities.data.datetime import OLDEST_QUOTE_DATE, DateVerifier, TradingDates
from olympus.securities.equities.data.price import *
from olympus.securities.equities.data.symbols import SymbolNotFoundError

# Standard run parameters:
# sudo su -s /bin/bash -c '... price.py' USER
# Optionally:
# '... price.py <current_run_username>'

class TestPrice(testing.Test):

    def setUp(self):
        if len(sys.argv) == 2:
            username = self.validRunUser(sys.argv[1])
        else:
            username = self.validRunUser(USER)
        self.adjustments = price.Adjustments(username)
        self.daily = price.Daily(username)
        self.weekly = price.Weekly(username)
        self.monthly = price.Monthly(username)
        self.intraday = price.Intraday(username)
        self.latest = price.Latest(username)
        self.mongo_data = data.Connection(username)
        self.date_utils = Dates()
        self.trading_dates = TradingDates()

    def test_adjustments(self):
        return #ALEX
        string = String()
        # Splits
        with self.assertRaises(SymbolNotFoundError):
            self.adjustments.splits(TEST_SYMBOL_FAKE)
        splits = self.adjustments.splits(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(splits.first())
        price_collection = 'price.' + TEST_SYMBOL_DIVSPLIT
        collection = self.mongo_data.db[price_collection]
        initial_split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0, 'Interval': 0 })
        splits = self.adjustments.splits(TEST_SYMBOL_DIVSPLIT,regen=True)
        last_split_date = None
        entry = splits.next()
        while entry is not None:
            # Verifying sort of splits
            if last_split_date is not None:
                self.assertLess(entry.date,last_split_date)
            last_split_date = entry.date
            entry = splits.next()
        # Check that data was regenerated
        first_regen_split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0, 'Interval': 0 })
        if initial_split_data is not None:
            self.assertGreater(first_regen_split_data['Time'],initial_split_data['Time'])
        # Dividends
        with self.assertRaises(SymbolNotFoundError):
            dividends = self.adjustments.dividends(TEST_SYMBOL_FAKE)
        dividends = self.adjustments.dividends(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(dividends.first())
        initial_dividend_data = collection.find_one({ 'Adjustment': 'Dividends' },{ '_id': 0, 'Interval': 0 })
        dividends = self.adjustments.dividends(TEST_SYMBOL_DIVSPLIT,regen=True)
        dividends.sort('date')
        last_dividend_date = None
        dividend = dividends.next()
        while dividend is not None:
            # Verifying reverse sort of dividends (see sort() a few lines ago)
            if last_dividend_date is not None:
                self.assertGreater(dividend.date,last_dividend_date)
            last_dividend_date = dividend.date
            dividend = dividends.next()
        regen_dividend_data = collection.find_one({ 'Adjustment': 'Dividends' },{ '_id': 0, 'Interval': 0 })
        # Regenerating dividend data should regenerate split data due to dependencies
        regen_split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0, 'Interval': 0 })
        self.assertGreater(regen_split_data['Time'],first_regen_split_data['Time'])
        if initial_dividend_data is not None:
            self.assertGreater(regen_dividend_data['Time'],initial_dividend_data['Time'])
        # Data checks for all returned adjustments and adjustment dates
        with self.assertRaises(SymbolNotFoundError):
            dividends = self.adjustments.adjustments(TEST_SYMBOL_FAKE)
        adjustments = self.adjustments.adjustments(TEST_SYMBOL_DIVSPLIT)
        adjustments_split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0, 'Interval': 0 })
        self.assertEqual(adjustments_split_data['Time'],regen_split_data['Time'])
        self.assertTrue(adjustments_split_data['Splits'] == regen_split_data['Splits'])
        adjustments_dividend_data = collection.find_one({ 'Adjustment': 'Dividends' },{ '_id': 0, 'Interval': 0 })
        self.assertEqual(adjustments_dividend_data['Time'],regen_dividend_data['Time'])
        self.assertTrue(adjustments_dividend_data['Dividends'] == regen_dividend_data['Dividends'])
        last_adjustment_date = None
        adjustment = adjustments.next()
        while adjustment is not None:
            timezone_date = self.date_utils.utc_date_to_timezone_date(adjustment.date,TIMEZONE)
            if last_adjustment_date is not None:
                self.assertLess(timezone_date,last_adjustment_date)
            last_adjustment_date = timezone_date
            if adjustment.get('dividend') is not None:
                dividend = dividends.get_by_attribute('date',timezone_date)
                self.assertEqual(timezone_date,dividend.date)
            if adjustment.get('price_adjustment') is not None:
                split = splits.get_by_attribute('date',timezone_date)
                self.assertEqual(timezone_date,split.date)
                self.assertEqual(adjustment.price_adjustment,split.price_dividend_adjustment)
                self.assertEqual(adjustment.volume_adjustment,split.volume_adjustment)
            adjustment = adjustments.next()
        adjustment_data = collection.find_one({ 'Adjustment': 'Merged' },{ '_id': 0, 'Interval': 0 })
        regen_adjustments = self.adjustments.adjustments(TEST_SYMBOL_DIVSPLIT,regen=True)
        regen_adjustment_data = collection.find_one({ 'Adjustment': 'Merged' },{ '_id': 0, 'Interval': 0 })
        self.assertGreater(regen_adjustment_data['Time'],adjustment_data['Time'])

    def test_daily(self):
        return #ALEX
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT)
        price_collection = 'price.' + TEST_SYMBOL_DIVSPLIT
        collection = self.mongo_data.db[price_collection]
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.daily.quote(TEST_SYMBOL_FAKE)
        quotes = self.daily.quote(TEST_SYMBOL_DIV,regen=True)
        # Compare returned data to database
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT)
        first_date = quotes.first().date
        init_quote_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0, 'Quotes': 0 })
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,regen=True)
        regen_quote_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0, 'Quotes': 0 })
        self.assertGreater(regen_quote_data['Time'],init_quote_data['Time'])
        # Check for invalid dates
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=dt(2022, 2, 29, 0, 0, 0).replace(tzinfo=tz.gettz(TIMEZONE)))
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,end_date=dt(2022, 2, 29, 0, 0, 0).replace(tzinfo=tz.gettz(TIMEZONE)))
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date='BADLYFORMATTEDDATE')
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,end_date='BADLYFORMATTEDDATE')
        tomorrow = (dt.now().astimezone() + timedelta(days=1)).replace(tzinfo=tz.gettz(TIMEZONE))
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=tomorrow)
        a_while_ago = (dt.now().astimezone() - timedelta(days=90)).replace(tzinfo=tz.gettz(TIMEZONE))
        today = dt.now().astimezone().replace(tzinfo=tz.gettz(TIMEZONE))
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=today,end_date=a_while_ago)
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='BADPERIOD')
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='1Y',start_date=a_while_ago)
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='1Y',end_date=a_while_ago)
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=a_while_ago,end_date=today)
        last_quote_time = None
        quote = quotes.next()
        while quote is not None:
            if last_quote_time is not None and quote.date.day == last_quote_time.day:
                # Extended hours quotes occasonally skip intervals, presumably because of a lack of trading activity
                if last_quote_time.hour >= 9 and last_quote_time.minute >=30 and last_quote_time.hour < 16:
                    self.assertEqual(self.intraday.DEFAULT_INTRADAY_FREQUENCY, int((quote.date - last_quote_time).total_seconds()/60))
            last_quote_time = quote.date
            quote = quotes.next()
        curr_range_date = None
        quote = quotes.next(reset=True)
        while quote is not None:
            # Verify returned data format and contents for a valid daily quote request
            if curr_range_date is None:
                self.assertGreaterEqual(quote.date,a_while_ago)
            if quote.adjusted_close is not None:
                self.assertLess(quote.adjusted_close,quote.close)
            if quote.adjusted_low is not None:
                self.assertLess(quote.adjusted_low,quote.low)
            if quote.adjusted_high is not None:
                self.assertLess(quote.adjusted_high,quote.high)
            if quote.adjusted_open is not None:
                self.assertLess(quote.adjusted_open,quote.open)
            if quote.adjusted_volume is not None:
                self.assertGreaterEqual(quote.adjusted_volume,quote.volume)
            self.assertGreaterEqual(quote.high,quote.close)
            self.assertGreater(quote.high,quote.low)
            self.assertGreaterEqual(quote.high,quote.open)
            self.assertLessEqual(quote.low,quote.close)
            self.assertLessEqual(quote.low,quote.open)
            curr_range_date = quote.date
            quote = quotes.next()
        self.assertLessEqual(curr_range_date,today)
        for period in VALID_DAILY_WEEKLY_PERIODS.keys():
            # Check range of raturned dates for all valid periods
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,period=period)
            first_period_date = quotes.first().date
            if period == 'All':
                self.assertEqual(first_date,first_period_date)
            else:    
                past_days = VALID_DAILY_WEEKLY_PERIODS[period] + 4 # Add 4 in case of mid-week day adjustment
                now = dt.now().astimezone()
                max_past_date = (dt(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=past_days)).replace(tzinfo=tz.gettz(TIMEZONE))
                self.assertLessEqual(max_past_date,first_period_date)
        # Remove the last price record by date, then get the quote again. Check that the record was restored.
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,regen=True)
        interval_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0 })
        last_date = None
        previous_date = None
        for quote_date in sorted(interval_data['Quotes'], key=lambda k: k[0], reverse=True):
            if last_date is None:
                last_date = self.date_utils.utc_date_to_timezone_date(quote_date[0],TIMEZONE)
                continue
            if previous_date is None:
                previous_date = self.date_utils.utc_date_to_timezone_date(quote_date[0],TIMEZONE)
                break
        if previous_date is not None:
            # Test for regeneration of missing dates by simulating the result from one trading day previous after doing full regen
            time_object = dt(previous_date.year, previous_date.month, previous_date.day, 23, 0, 0).replace(tzinfo=tz.gettz())
            collection.update_one( { 'Interval': '1d', 'Quotes': { '$elemMatch': { '0': { '$eq': last_date  } } } }, { '$unset': { "Quotes.$": 1 } })
            collection.update_one( { 'Interval': '1d' }, { '$pull': { 'Quotes': None } } )
            collection.update_one({ 'Interval': '1d' }, { "$set":  { 'End Date': previous_date, 'Time': time_object }})
            data = collection.find_one({ 'Interval': '1d' } , { 'Quotes': { '$elemMatch': { '0': { '$eq': last_date } } } })
            self.assertFalse('Quotes' in data)
            data = collection.find_one({ 'Interval': '1d' } , { 'Quotes': { '$elemMatch': { '0': { '$eq': previous_date } } } })
            self.assertTrue('Quotes' in data)
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT)
            data = collection.find_one({ 'Interval': '1d' } , { 'Quotes': { '$elemMatch': { '0': { '$eq': last_date } } } })
            self.assertTrue('Quotes' in data)
    
    def test_weekly(self):
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.weekly.quote(TEST_SYMBOL_FAKE)
        quotes = self.weekly.quote(TEST_SYMBOL_DIVSPLIT,'All')
        first_date = quotes.first().date
        quote = quotes.next()
        while quote is not None:
            # Verify returned data for a valid weekly quote request
            if quote.adjusted_close is not None:
                self.assertLessEqual(quote.adjusted_close,quote.close)
            if quote.adjusted_low is not None:
                self.assertLessEqual(quote.adjusted_low,quote.low)
            if quote.adjusted_high is not None:
                self.assertLessEqual(quote.adjusted_high,quote.high)
            if quote.adjusted_open is not None:
                self.assertLessEqual(quote.adjusted_open,quote.open)
            if quote.adjusted_volume is not None:
                self.assertGreaterEqual(quote.adjusted_volume,quote.volume)
            self.assertGreaterEqual(quote.high,quote.close)
            self.assertGreaterEqual(quote.high,quote.low)
            self.assertGreaterEqual(quote.high,quote.open)
            self.assertLessEqual(quote.low,quote.close)
            self.assertLessEqual(quote.low,quote.open)
            quote = quotes.next()
        for period in VALID_DAILY_WEEKLY_PERIODS.keys():
            if period == 'All':
                continue
            # Verify returned date ranges for all valid periods
            past_days = VALID_DAILY_WEEKLY_PERIODS[period] + 4 # Add 4 in case of weekday adjustment
            max_past_date = (dt.now().astimezone() - timedelta(days=past_days)).replace(tzinfo=tz.gettz(TIMEZONE))
            quotes = self.weekly.quote(TEST_SYMBOL_DIV,period)
            first_period_date = quotes.first().date
            self.assertLessEqual(first_date,first_period_date)
            self.assertLessEqual(max_past_date,first_period_date)

    def test_monthly(self):
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.monthly.quote(TEST_SYMBOL_FAKE)
        quotes = self.monthly.quote(TEST_SYMBOL_DIVSPLIT,period='All')
        first_date = quotes.first().date
        quote = quotes.next()
        while quote is not None:
            # Verify returned data for a valid monthly quote request
            if quote.adjusted_close is not None:
                self.assertLessEqual(quote.adjusted_close,quote.close)
            if quote.adjusted_low is not None:
                self.assertLessEqual(quote.adjusted_low,quote.low)
            if quote.adjusted_high is not None:
                self.assertLessEqual(quote.adjusted_high,quote.high)
            if quote.adjusted_open is not None:
                self.assertLessEqual(quote.adjusted_open,quote.open)
            if quote.adjusted_volume is not None:
                self.assertGreaterEqual(quote.adjusted_volume,quote.volume)
            self.assertGreaterEqual(quote.high,quote.close)
            self.assertGreaterEqual(quote.high,quote.low)
            self.assertGreaterEqual(quote.high,quote.open)
            self.assertLessEqual(quote.low,quote.close)
            self.assertLessEqual(quote.low,quote.open)
            quote = quotes.next()
        for period in VALID_MONTHLY_PERIODS:
            if period == 'All':
                continue
            # Verify returned date ranges for all valid periods
            past_period = int(re.sub(r"[Y]", "", period))
            now = dt.now().astimezone()
            max_past_date = dt(now.year - int(past_period),now.month,1,0,0,0).replace(tzinfo=tz.gettz(TIMEZONE))
            quotes = self.monthly.quote(TEST_SYMBOL_DIVSPLIT,period)
            first_period_date = quotes.first().date
            self.assertLessEqual(first_date,first_period_date)
            self.assertLessEqual(max_past_date,first_period_date)

    def test_latest(self):
        return #ALEX
        result = self.latest.quote(TEST_SYMBOL_DIV.lower())
        symbol = TEST_SYMBOL_DIV.upper()
        # Verify returned data format and contents
        self.assertIsNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        quote = result.get_symbol(TEST_SYMBOL_DIV)
        quoteTimeLong = int(time.time() * 1000)
        self.assertEqual(quote.symbol, symbol)
        self.assertEqual(quote.exchange, TEST_SYMBOL_DIV_QUOTE_EXCHANGE)
        self.assertEqual(quote.exchange_name, TEST_SYMBOL_DIV_QUOTE_EXCHANGE_NAME)
        self.assertGreaterEqual(quote.ask, quote.bid)
        self.assertGreaterEqual(quote.high, quote.low)
        self.assertGreaterEqual(quote.high, quote.open)
        self.assertLessEqual(quote.low, quote.open)
        self.assertGreaterEqual(quoteTimeLong, quote.quote_time_in_long)
        self.assertGreaterEqual(quoteTimeLong, quote.trade_time_in_long)
        self.assertGreaterEqual(quoteTimeLong, quote.regular_market_trade_time_in_long)
        self.assertGreaterEqual(quote.trade_time_in_long, quote.regular_market_trade_time_in_long)
        self.assertLessEqual(abs(round(quote.net_change - (quote.last_price - quote.close),2)), .01)
        # Mixed request including (1) Valid symbol, (2) Valid but incorrectly cased symbol, and (3) Unknown symbol
        result = self.latest.quote([TEST_SYMBOL_NODIVSPLIT.lower(),TEST_SYMBOL_DIVSPLIT,TEST_SYMBOL_FAKE.lower()])
        quoteTimeLong = int(time.time() * 1000)
        self.assertIsNotNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        self.assertEqual(len(result.unknown_symbols), 1)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        for symbol in [TEST_SYMBOL_NODIVSPLIT, TEST_SYMBOL_DIVSPLIT]:
            quote = result.get_symbol(symbol)
            self.assertEqual(quote.symbol, symbol)
            if symbol == TEST_SYMBOL_NODIVSPLIT:
                self.assertEqual(quote.exchange, TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE)
                self.assertEqual(quote.exchange_name, TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE_NAME)
            else:
                self.assertEqual(quote.exchange, TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE)
                self.assertEqual(quote.exchange_name, TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE_NAME)
            self.assertGreaterEqual(quote.ask, quote.bid)
            self.assertGreaterEqual(quote.high, quote.low)
            self.assertGreaterEqual(quote.high, quote.open)
            self.assertLessEqual(quote.low, quote.open)
            self.assertGreaterEqual(quoteTimeLong, quote.quote_time_in_long)
            self.assertGreaterEqual(quoteTimeLong, quote.trade_time_in_long)
            self.assertGreaterEqual(quoteTimeLong, quote.regular_market_trade_time_in_long)
            self.assertGreaterEqual(quote.trade_time_in_long, quote.regular_market_trade_time_in_long)
            self.assertLessEqual(abs(round(quote.net_change - (quote.last_price - quote.close),2)), .01)
        # Request including only unknown symbols
        result = self.latest.quote([TEST_SYMBOL_FAKE,TEST_SYMBOL_FAKE_TWO.lower()])
        self.assertIsNone(result.get_quotes())
        self.assertIsNotNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        self.assertEqual(len(result.unknown_symbols), 2)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE_TWO in result.unknown_symbols)

    def test_intraday(self):
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            self.intraday.quote(TEST_SYMBOL_FAKE)
        # Check for valid frequencies and periods
        bad_min_frequency = min(self.intraday.VALID_INTRADAY_FREQUENCIES.keys()) - 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,frequency=bad_min_frequency)
        bad_max_frequency = max(self.intraday.VALID_INTRADAY_FREQUENCIES.keys()) + 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,frequency=bad_max_frequency)
        bad_min_period = min(self.intraday.VALID_INTRADAY_PERIODS) - 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,period=bad_min_period)
        bad_max_period = max(self.intraday.VALID_INTRADAY_PERIODS) + 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,period=bad_max_period)
        for frequency in self.intraday.VALID_INTRADAY_FREQUENCIES:
            self.intraday.valid_frequency(frequency)
        for period in self.intraday.VALID_INTRADAY_PERIODS:
            self.intraday.valid_period(period)
        period = self.intraday.valid_period() # period can be none
        self.assertEqual(period,self.intraday.DEFAULT_INTRADAY_PERIOD)
        # The next two series use the default values for period and frequency
        quotes = self.intraday.quote(TEST_SYMBOL_DIV)
        quote = quotes.next()
        last_quote_time = None
        while quote is not None:
            if last_quote_time is not None and quote.date.day == last_quote_time.day:
                # Extended hours quotes occasonally skip intervals, presumably because of a lack of trading activity
                if last_quote_time.hour >= 9 and last_quote_time.minute >=30 and last_quote_time.hour < 16:
                    self.assertEqual(self.intraday.DEFAULT_INTRADAY_FREQUENCY, int((quote.date - last_quote_time).total_seconds()/60))
            last_quote_time = quote.date
            quote = quotes.next()
        quotes = self.intraday.quote(TEST_SYMBOL_DIV,need_extended_hours_data=False)
        quote = quotes.next()
        last_quote_time = None
        while quote is not None:
            if last_quote_time is None:
                half_days = self.trading_dates.half_days(quote.date)
            if last_quote_time is None or quote.date.day > last_quote_time.day or quote.date.month > last_quote_time.month:
                self.assertEqual(REGULAR_MARKET_OPEN_TIME,quote.date.strftime("%H:%M:%S"))
            if last_quote_time is not None and (quote.date.day > last_quote_time.day or quote.date.month > last_quote_time.month):
                yesterday_close_time_string = (last_quote_time + timedelta(minutes=self.intraday.DEFAULT_INTRADAY_FREQUENCY)).strftime("%H:%M:%S")
                midnight_quote_date = dt(quote.date.year, quote.date.month, quote.date.day, 0, 0, 0).replace(tzinfo=tz.gettz(TIMEZONE))
                if half_days is None or midnight_quote_date not in half_days:
                    self.assertEqual(REGULAR_MARKET_CLOSE_TIME,yesterday_close_time_string)
                else:
                    self.assertEqual(SHORTENED_MARKET_CLOSE_TIME,yesterday_close_time_string)
            last_quote_time = quote.date
            quote = quotes.next()
        today = dt.now().astimezone()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        for period in self.intraday.VALID_INTRADAY_PERIODS:
            with self.assertRaises(Exception):
                # Cannot specify period and start_date together
                self.intraday.quote(TEST_SYMBOL_DIVSPLIT,period=period,start_date=two_days_ago)
            # Check all period/frequency combinations
            for frequency in self.intraday.VALID_INTRADAY_FREQUENCIES:
                # If we have an end date, the number of available periods will be limited based on the frequency of data requested.
                # Here we generate this error (or another date error)
                oldest_available_date = self.intraday.oldest_available_date(frequency)
                error_date = oldest_available_date + timedelta(days=period-2)
                with self.assertRaises(Exception):
                    self.intraday.quote(TEST_SYMBOL_NODIVSPLIT,need_extended_hours_data=False,period=period,frequency=frequency,end_date=error_date)
                # The next series is limited to regular trading hours to ensure there are no time periods with no data
                quotes = self.intraday.quote(TEST_SYMBOL_DIVSPLIT,period=period,frequency=frequency,need_extended_hours_data=False)
                last_quote_time = None
                quote = quotes.next()
                while quote is not None:
                    if last_quote_time is not None and quote.date.year == last_quote_time.year and quote.date.month == last_quote_time.month and quote.date.day == last_quote_time.day:
                        self.assertEqual(frequency, int((quote.date - last_quote_time).total_seconds()/60))
                    last_quote_time = quote.date
                    quote = quotes.next()
        # Checks for bad absolute and relative dates
        too_old_date = OLDEST_QUOTE_DATE - timedelta(days=1)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,start_date=too_old_date)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=too_old_date)
        tomorrow = dt.now().astimezone() + timedelta(days=1)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,start_date=tommorow)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=tomorrow)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=two_days_ago,start_date=yesterday)
        for frequency in self.intraday.VALID_INTRADAY_FREQUENCIES:
            earliest_available_date = self.intraday.oldest_available_date(frequency)
            too_early = earliest_available_date - timedelta(days=1)
            day_delta = round((dt.now().astimezone() - dt(earliest_available_date.year, earliest_available_date.month, earliest_available_date.day).replace(tzinfo=tz.gettz())).days / 2)
            half_way_end_date = dt.now().astimezone() - timedelta(days=day_delta)
            # Checks for dates that are too early when combined with a frequency
            with self.assertRaises(Exception):
                self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,start_date=too_early)
            with self.assertRaises(Exception):
                self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,end_date=too_early)
            # Proper date ranges
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,start_date=earliest_available_date)
            first_quote = quotes.first()
            last_quote = quotes.last()
            self.assertGreaterEqual(first_quote.date,earliest_available_date)
            self.assertGreaterEqual(today,last_quote.date)
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,end_date=half_way_end_date)
            last_quote = quotes.last()
            # We convert these dates to midnight because the API will return a full day's price date regardless of the exact time of day requested as an end date
            midnight_half_way_end_date = dt(half_way_end_date.year, half_way_end_date.month, half_way_end_date.day, 0, 0, 0).replace(tzinfo=tz.gettz())
            midnight_last_quote_date = dt(last_quote.date.year, last_quote.date.month, last_quote.date.day, 0, 0, 0).replace(tzinfo=tz.gettz())
            self.assertGreaterEqual(midnight_half_way_end_date,midnight_last_quote_date)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
