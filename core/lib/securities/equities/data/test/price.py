#!/usr/bin/env python3

import json, jsonschema, os, re, sys, time, unittest

from datetime import date, timedelta
from datetime import datetime as dt
from jsonschema import validate

import olympus.securities.equities.data as data
import olympus.securities.equities.data.price as price
import olympus.testing as testing

from olympus import String, USER
from olympus.securities.equities import *
from olympus.securities.equities.data.datetime import OLDEST_QUOTE_DATE, DateVerifier
from olympus.securities.equities.data.price import DEFAULT_INTRADAY_FREQUENCY, DEFAULT_INTRADAY_PERIOD, PRICE_FORMAT, SPLIT_FORMAT, VALID_DAILY_WEEKLY_PERIODS, VALID_INTRADAY_FREQUENCIES, VALID_INTRADAY_PERIODS, VALID_MONTHLY_PERIODS
from olympus.securities.equities.data.symbols import SymbolNotFoundError

QUOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "Adjusted Close": { "type": "number" },
        "Adjusted High": { "type": "number" },
        "Adjusted Low": { "type": "number" },
        "Adjusted Open": { "type": "number" },
        "Adjusted Volume": { "type": "integer" },
        "Close": { "type": "number" },
        "High": { "type": "number" },
        "Low": { "type": "number" },
        "Open": { "type": "number" },
        "Volume": { "type": "integer" } 
    },
    "required": [
        "Adjusted Close",
        "Adjusted High",
        "Adjusted Low",
        "Adjusted Open",
        "Adjusted Volume",
        "Close",
        "High",
        "Low",
        "Open",
        "Volume"
    ]
}

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

    def test_adjustments(self):
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
        string = String()
        while entry is not None:
            if last_split_date is not None:
                self.assertLess(entry.datetime,last_split_date)
            for split_attribute in list(SPLIT_FORMAT.keys()):
                self.assertEqual(type(getattr(entry,string.pascal_case_to_underscore(split_attribute))),SPLIT_FORMAT[split_attribute])
            last_split_date = entry.datetime
            entry = splits.next()
        return #ALEX
        dividend_schema = {
            "type": "object",
            "properties": {
                "Adjusted Dividend": {
                    "type": "number"
                },
                "Dividend": {
                    "type": "number"
                }
            },
            "required": [
                "Adjusted Dividend",
                "Dividend"
            ]
        }
        # Data checks for all returned split dates
        first_regen_split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0, 'Interval': 0 })
        if initial_split_data is not None:
            self.assertGreater(first_regen_split_data['Time'],initial_split_data['Time'])
        # Data checks for all returned dividend dates
        with self.assertRaises(SymbolNotFoundError):
            dividends = self.adjustments.dividends(TEST_SYMBOL_FAKE)
        dividends = self.adjustments.dividends(TEST_SYMBOL_SPLIT)
        self.assertIsNone(dividends)
        initial_dividend_data = collection.find_one({ 'Adjustment': 'Dividends' },{ '_id': 0, 'Interval': 0 })
        dividends = self.adjustments.dividends(TEST_SYMBOL_DIVSPLIT,regen=True)
        last_dividend_date = None
        for dividend_date in dividends:
            validate(instance=dividends[dividend_date],schema=dividend_schema)
            if last_dividend_date is not None:
                self.assertLess(dividend_date,last_dividend_date)
            last_dividend_date = dividend_date
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
        for adjustment in adjustments:
            if last_adjustment_date is not None:
                self.assertLess(adjustment['Date'],last_adjustment_date)
            last_adjustment_date = adjustment['Date']
            if 'Dividend' in adjustment:
                self.assertEqual(adjustment['Dividend'],dividends[adjustment['Date']]['Adjusted Dividend'])
            if 'Price Adjustment' in adjustment:
                self.assertEqual(adjustment['Price Adjustment'],splits[adjustment['Date']]['Price/Dividend Adjustment'])
                self.assertEqual(adjustment['Volume Adjustment'],splits[adjustment['Date']]['Volume Adjustment'])
        adjustment_data = collection.find_one({ 'Adjustment': 'Merged' },{ '_id': 0, 'Interval': 0 })
        regen_adjustments = self.adjustments.adjustments(TEST_SYMBOL_DIVSPLIT,regen=True)
        regen_adjustment_data = collection.find_one({ 'Adjustment': 'Merged' },{ '_id': 0, 'Interval': 0 })
        self.assertGreater(regen_adjustment_data['Time'],adjustment_data['Time'])

    def test_daily(self):
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.daily.quote(TEST_SYMBOL_FAKE)
        # Compare returned data to database
        price_collection = 'price.' + TEST_SYMBOL_DIVSPLIT
        collection = self.mongo_data.db[price_collection]
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT)
        first_date = list(quotes)[0]
        init_quote_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0, 'Quotes': 0 })
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,regen=True)
        regen_quote_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0, 'Quotes': 0 })
        self.assertGreater(regen_quote_data['Time'],init_quote_data['Time'])
        # Check for invalid dates
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date='2022-02-29')
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,end_date='2022-02-29')
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date='BADLYFORMATTEDDATE')
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,end_date='BADLYFORMATTEDDATE')
        tomorrow = str(date.today() + timedelta(days=1))
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=tomorrow)
        a_while_ago = str(date.today() - timedelta(days=90))
        today = str(date.today())
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=today,end_date=a_while_ago)
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='BADPERIOD')
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='1Y',start_date=a_while_ago)
        with self.assertRaises(Exception):
            self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='1Y',end_date=a_while_ago)
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=a_while_ago,end_date=today)
        curr_range_date = None
        for range_date in quotes:
            # Verify returned data format and contents for a valid daily quote request
            if curr_range_date is None:
                self.assertGreaterEqual(range_date,a_while_ago)
            validate(instance=quotes[range_date],schema=QUOTE_SCHEMA)
            self.assertLessEqual(quotes[range_date]['Adjusted Close'],quotes[range_date]['Close'])
            self.assertLessEqual(quotes[range_date]['Adjusted Low'],quotes[range_date]['Low'])
            self.assertLessEqual(quotes[range_date]['Adjusted High'],quotes[range_date]['High'])
            self.assertLessEqual(quotes[range_date]['Adjusted Open'],quotes[range_date]['Open'])
            self.assertGreaterEqual(quotes[range_date]['Adjusted Volume'],quotes[range_date]['Volume'])
            self.assertGreaterEqual(quotes[range_date]['High'],quotes[range_date]['Close'])
            self.assertGreaterEqual(quotes[range_date]['High'],quotes[range_date]['Low'])
            self.assertGreaterEqual(quotes[range_date]['High'],quotes[range_date]['Open'])
            self.assertLessEqual(quotes[range_date]['Low'],quotes[range_date]['Close'])
            self.assertLessEqual(quotes[range_date]['Low'],quotes[range_date]['Open'])
            curr_range_date = range_date
        self.assertLessEqual(curr_range_date,today)
        for period in VALID_DAILY_WEEKLY_PERIODS.keys():
            # Check range of raturned dates for all valid periods
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,period=period)
            first_period_date = list(quotes)[0]
            if period == 'All':
                self.assertEqual(first_date,first_period_date)
            else:    
                past_days = VALID_DAILY_WEEKLY_PERIODS[period] + 4 # Add 4 in case of mid-week day adjustment
                max_past_date = str(date.today() - timedelta(days=past_days))
                self.assertLessEqual(max_past_date,first_period_date)
        # Remove the last price record by date, then get the quote again. Check that the record was restored.
        interval_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0 })
        last_date = None
        previous_date = None
        for quote_date in sorted(interval_data['Quotes']):
            previous_date = last_date
            if last_date is None or last_date < quote_date:
                last_date = quote_date
        if previous_date is not None:
            last_quote_saved = interval_data['Quotes'][last_date]
            # Test for regeneration of missing dates by simulating the result from one trading day
            # previous after doing full regen
            year,month,day = map(int,previous_date.split('-'))
            time_string = "%d-%02d-%02d 00:00:00.000000-04:00" % (year,month,day)
            collection.update_one({ 'Interval': '1d' },{ "$unset": { 'Quotes.'+last_date: 1 }})
            collection.update_one({ 'Interval': '1d' },{ "$set":  { 'End Date': previous_date, 'Time': time_string }})
            interval_data = collection.find_one({ 'Interval': '1d',  },{ '_id': 0, 'Interval': 0 })
            self.assertTrue(previous_date in interval_data['Quotes']);
            self.assertFalse(last_date in interval_data['Quotes']);
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT)
            self.assertTrue(last_date in quotes);
    
    def test_weekly(self):
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.daily.quote(TEST_SYMBOL_FAKE)
        today = str(date.today())
        quotes = self.weekly.quote(TEST_SYMBOL_DIVSPLIT,'All')
        first_date = list(quotes)[0]
        for quote_date in quotes:
            # Verify returned data format and contents for a valid weekly quote request
            validate(instance=quotes[quote_date],schema=QUOTE_SCHEMA)
            self.assertLessEqual(quotes[quote_date]['Adjusted Close'],quotes[quote_date]['Close'])
            self.assertLessEqual(quotes[quote_date]['Adjusted Low'],quotes[quote_date]['Low'])
            self.assertLessEqual(quotes[quote_date]['Adjusted High'],quotes[quote_date]['High'])
            self.assertLessEqual(quotes[quote_date]['Adjusted Open'],quotes[quote_date]['Open'])
            self.assertGreaterEqual(quotes[quote_date]['Adjusted Volume'],quotes[quote_date]['Volume'])
            self.assertGreaterEqual(quotes[quote_date]['High'],quotes[quote_date]['Close'])
            self.assertGreaterEqual(quotes[quote_date]['High'],quotes[quote_date]['Low'])
            self.assertGreaterEqual(quotes[quote_date]['High'],quotes[quote_date]['Open'])
            self.assertLessEqual(quotes[quote_date]['Low'],quotes[quote_date]['Close'])
            self.assertLessEqual(quotes[quote_date]['Low'],quotes[quote_date]['Open'])
        for period in VALID_DAILY_WEEKLY_PERIODS.keys():
            if period == 'All':
                continue
            # Verify returned date ranges for all valid periods
            past_days = VALID_DAILY_WEEKLY_PERIODS[period] + 4 # Add 4 in case of weekday adjustment
            max_past_date = str(date.today() - timedelta(days=past_days))
            quotes = self.weekly.quote(TEST_SYMBOL_DIV,period)
            first_period_date = list(quotes)[0]
            self.assertLessEqual(first_date,first_period_date)
            self.assertLessEqual(max_past_date,first_period_date)

    def test_monthly(self):
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.monthly.quote(TEST_SYMBOL_FAKE)
        today = str(date.today())
        quotes = self.monthly.quote(TEST_SYMBOL_DIVSPLIT,period='All')
        first_date = list(quotes)[0]
        for quote_date in quotes:
            # Verify returned data format and contents for a valid monthly quote request
            validate(instance=quotes[quote_date],schema=QUOTE_SCHEMA)
            self.assertLessEqual(quotes[quote_date]['Adjusted Close'],quotes[quote_date]['Close'])
            self.assertLessEqual(quotes[quote_date]['Adjusted Low'],quotes[quote_date]['Low'])
            self.assertLessEqual(quotes[quote_date]['Adjusted High'],quotes[quote_date]['High'])
            self.assertLessEqual(quotes[quote_date]['Adjusted Open'],quotes[quote_date]['Open'])
            self.assertGreaterEqual(quotes[quote_date]['Adjusted Volume'],quotes[quote_date]['Volume'])
            self.assertGreaterEqual(quotes[quote_date]['High'],quotes[quote_date]['Close'])
            self.assertGreaterEqual(quotes[quote_date]['High'],quotes[quote_date]['Low'])
            self.assertGreaterEqual(quotes[quote_date]['High'],quotes[quote_date]['Open'])
            self.assertLessEqual(quotes[quote_date]['Low'],quotes[quote_date]['Close'])
            self.assertLessEqual(quotes[quote_date]['Low'],quotes[quote_date]['Open'])
        for period in VALID_MONTHLY_PERIODS:
            if period == 'All':
                continue
            # Verify returned date ranges for all valid periods
            past_period = int(re.sub(r"[Y]", "", period))
            now = dt.now().astimezone()
            max_past_date = "%d-%02d-%02d" % (now.year - int(past_period),now.month,1)
            quotes = self.monthly.quote(TEST_SYMBOL_DIVSPLIT,period)
            first_period_date = list(quotes)[0]
            self.assertLessEqual(first_date,first_period_date)
            self.assertLessEqual(max_past_date,first_period_date)

    def test_latest(self):
        return #ALEX
        result = self.latest.quote(TEST_SYMBOL_DIV.lower(),verify_response_format=True)
        symbol = TEST_SYMBOL_DIV.upper()
        # Verify returned data format and contents
        self.assertIsNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        quote = result.get_symbol(TEST_SYMBOL_DIV)
        quoteTimeLong = int(time.time() * 1000)
        self.assertEqual(quote.symbol, symbol)
        self.assertEqual(quote.misc.exchange, TEST_SYMBOL_DIV_QUOTE_EXCHANGE)
        self.assertEqual(quote.misc.exchange_name, TEST_SYMBOL_DIV_QUOTE_EXCHANGE_NAME)
        self.assertGreaterEqual(quote.misc.ask, quote.misc.bid)
        self.assertGreaterEqual(quote.high, quote.low)
        self.assertGreaterEqual(quote.high, quote.open)
        self.assertLessEqual(quote.low, quote.open)
        self.assertGreaterEqual(quoteTimeLong, quote.misc.quote_time_in_long)
        self.assertGreaterEqual(quoteTimeLong, quote.misc.trade_time_in_long)
        self.assertGreaterEqual(quoteTimeLong, quote.misc.regular_market_trade_time_in_long)
        self.assertGreaterEqual(quote.misc.trade_time_in_long, quote.misc.regular_market_trade_time_in_long)
        self.assertLessEqual(abs(round(quote.misc.net_change - (quote.misc.last_price - quote.close),2)), .01)
        # Mixed request including (1) Valid symbol, (2) Valid but incorrectly cased symbol, and (3) Unknown symbol
        result = self.latest.quote([TEST_SYMBOL_NODIVSPLIT.lower(),TEST_SYMBOL_DIVSPLIT,TEST_SYMBOL_FAKE.lower()],verify_response_format=True)
        quoteTimeLong = int(time.time() * 1000)
        self.assertIsNotNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        self.assertEqual(len(result.unknown_symbols), 1)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        for symbol in [TEST_SYMBOL_NODIVSPLIT, TEST_SYMBOL_DIVSPLIT]:
            quote = result.get_symbol(symbol)
            self.assertEqual(quote.symbol, symbol)
            if symbol == TEST_SYMBOL_NODIVSPLIT:
                self.assertEqual(quote.misc.exchange, TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE)
                self.assertEqual(quote.misc.exchange_name, TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE_NAME)
            else:
                self.assertEqual(quote.misc.exchange, TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE)
                self.assertEqual(quote.misc.exchange_name, TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE_NAME)
            self.assertGreaterEqual(quote.misc.ask, quote.misc.bid)
            self.assertGreaterEqual(quote.high, quote.low)
            self.assertGreaterEqual(quote.high, quote.open)
            self.assertLessEqual(quote.low, quote.open)
            self.assertGreaterEqual(quoteTimeLong, quote.misc.quote_time_in_long)
            self.assertGreaterEqual(quoteTimeLong, quote.misc.trade_time_in_long)
            self.assertGreaterEqual(quoteTimeLong, quote.misc.regular_market_trade_time_in_long)
            self.assertGreaterEqual(quote.misc.trade_time_in_long, quote.misc.regular_market_trade_time_in_long)
            self.assertLessEqual(abs(round(quote.misc.net_change - (quote.misc.last_price - quote.close),2)), .01)
        # Request including only unknown symbols
        result = self.latest.quote([TEST_SYMBOL_FAKE,TEST_SYMBOL_FAKE_TWO.lower()])
        self.assertIsNone(result.symbols)
        self.assertIsNotNone(result.unknown_symbols)
        self.assertIsNone(result.unquoted_symbols)
        self.assertEqual(len(result.unknown_symbols), 2)
        self.assertTrue(TEST_SYMBOL_FAKE in result.unknown_symbols)
        self.assertTrue(TEST_SYMBOL_FAKE_TWO in result.unknown_symbols)

    def test_intraday(self):
        return #ALEX
        date_verifier = DateVerifier()
        two_days_ago = (dt.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        today = dt.now().strftime("%Y-%m-%d")
        yesterday = (dt.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        with self.assertRaises(SymbolNotFoundError):
            self.intraday.quote(TEST_SYMBOL_FAKE)
        # Check for valid frequencies and periods
        bad_min_frequency = min(VALID_INTRADAY_FREQUENCIES.keys()) - 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,frequency=bad_min_frequency)
        bad_max_frequency = max(VALID_INTRADAY_FREQUENCIES.keys()) + 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,frequency=bad_max_frequency)
        bad_min_period = min(VALID_INTRADAY_PERIODS) - 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,period=bad_min_period)
        bad_max_period = max(VALID_INTRADAY_PERIODS) + 1
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_DIV,period=bad_max_period)
        for frequency in VALID_INTRADAY_FREQUENCIES:
            self.intraday.valid_frequency(frequency)
        for period in VALID_INTRADAY_PERIODS:
            self.intraday.valid_period(period)
        period = self.intraday.valid_period() # period can be none
        self.assertEqual(period,DEFAULT_INTRADAY_PERIOD)
        # The next two series use the default values for period and frequency
        quotes = self.intraday.quote(TEST_SYMBOL_DIV)
        self.assertEqual(DEFAULT_INTRADAY_PERIOD,len(quotes.keys()))
        for quote_date in quotes:
            date_verifier.verify_date(quote_date)
            last_quote_time = None
            for quote_time in quotes[quote_date]:
                # Check for valid keys in returned data with no missing keys
                for quote_key in PRICE_FORMAT:
                    self.assertKeyInDict(quote_key,quotes[quote_date][quote_time])
                for quote_date_key in quotes[quote_date][quote_time]:
                    self.assertKeyInDict(quote_date_key,PRICE_FORMAT)
                if last_quote_time is not None:
                    previous_date_time = dt.strptime(quote_date + ' ' + last_quote_time, "%Y-%m-%d %H:%M:%S")
                    current_date_time = dt.strptime(quote_date + ' ' + quote_time, "%Y-%m-%d %H:%M:%S")
                    self.assertEqual(DEFAULT_INTRADAY_FREQUENCY, int((current_date_time - previous_date_time).total_seconds()/60))
                    last_quote_time = quote_time
        quotes = self.intraday.quote(TEST_SYMBOL_DIV,need_extended_hours_data=False)
        for quote_date in quotes:
            open_time = list(quotes[quote_date].keys())[0]
            self.assertEqual(open_time,REGULAR_MARKET_OPEN_TIME)
            close_time = dt.strptime(quote_date + ' ' + REGULAR_MARKET_CLOSE_TIME, "%Y-%m-%d %H:%M:%S")
            last_quote_time = list(quotes[quote_date].keys())[-1]
            last_time = dt.strptime(quote_date + ' ' + last_quote_time, "%Y-%m-%d %H:%M:%S")
            self.assertEqual(close_time,last_time + timedelta(minutes=DEFAULT_INTRADAY_FREQUENCY))
        for period in VALID_INTRADAY_PERIODS:
            with self.assertRaises(Exception):
                # Cannot specify period and start_date together
                self.intraday.quote(TEST_SYMBOL_DIVSPLIT,period=period,start_date=two_days_ago)
            # Check all period/frequency combinations
            for frequency in VALID_INTRADAY_FREQUENCIES:
                # If we have an end date, the number of available periods will be limited based on the frequency of data requested.
                # Here we generate this error (or another date error)
                oldest_available_date = self.intraday.oldest_available_date(frequency)
                error_date = (dt.strptime(oldest_available_date,"%Y-%m-%d") + timedelta(days=period-2)).strftime("%Y-%m-%d")
                with self.assertRaises(Exception):
                    self.intraday.quote(TEST_SYMBOL_NODIVSPLIT,need_extended_hours_data=False,period=period,frequency=frequency,end_date=error_date)
                quotes = self.intraday.quote(TEST_SYMBOL_DIVSPLIT,period=period,frequency=frequency)
                self.assertEqual(period,len(quotes.keys()))
                for quote_date in quotes:
                    last_quote_time = None
                    for quote_time in quotes[quote_date]:
                        if last_quote_time is not None:
                            previous_date_time = dt.strptime(quote_date + ' ' + last_quote_time, "%Y-%m-%d %H:%M:%S")
                            current_date_time = dt.strptime(quote_date + ' ' + quote_time, "%Y-%m-%d %H:%M:%S")
                            self.assertEqual(frequency, int((current_date_time - previous_date_time).total_seconds()/60))
                            last_quote_time = quote_time
        # Checks for bad absolute and relative dates
        too_old_date = (dt.strptime(OLDEST_QUOTE_DATE, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,start_date=too_old_date)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=too_old_date)
        tomorrow = (dt.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,start_date=tommorow)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=tomorrow)
        with self.assertRaises(Exception):
            self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=two_days_ago,start_date=yesterday)
        for frequency in VALID_INTRADAY_FREQUENCIES:
            earliest_available_date = self.intraday.oldest_available_date(frequency)
            too_early = (dt.strptime(earliest_available_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            day_delta = round((dt.now() - dt(day=int(earliest_available_date[-2:]), month=int(earliest_available_date[-5:-3]), year=int(earliest_available_date[:4]))).days / 2)
            half_way_end_date = (dt.now() - timedelta(days=day_delta)).strftime("%Y-%m-%d")
            # Checks for dates that are too early when combined with a frequency
            with self.assertRaises(Exception):
                self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,start_date=too_early)
            with self.assertRaises(Exception):
                self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,end_date=too_early)
            # Proper date ranges
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,start_date=earliest_available_date)
            self.assertGreaterEqual(list(quotes.keys())[0],earliest_available_date)
            self.assertGreaterEqual(today,list(quotes.keys())[-1])
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,frequency=frequency,end_date=half_way_end_date)
            self.assertGreaterEqual(half_way_end_date,list(quotes.keys())[-1])

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
