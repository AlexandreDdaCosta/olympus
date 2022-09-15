#!/usr/bin/env python3

import json, jsonschema, os, re, sys, time, unittest

from datetime import date, timedelta
from datetime import datetime as dt
from jsonschema import validate

import olympus.securities.equities.data as data
import olympus.securities.equities.data.price as price
import olympus.testing as testing

from olympus import USER
from olympus.securities.equities import *
from olympus.securities.equities.data.datetime import OLDEST_QUOTE_DATE, DateVerifier
from olympus.securities.equities.data.price import DEFAULT_INTRADAY_FREQUENCY, DEFAULT_INTRADAY_PERIOD, PRICE_FORMAT, VALID_DAILY_WEEKLY_PERIODS, VALID_INTRADAY_FREQUENCIES, VALID_INTRADAY_PERIODS, VALID_MONTHLY_PERIODS
from olympus.securities.equities.data.symbols import SymbolNotFoundError

LATEST_PRICE_SCHEMA_FILE = re.sub(r'(.*\/).*\/.*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/LatestPriceQuote.json'
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
        split_schema = {
            "type": "object",
            "properties": {
                "Denominator": {
                    "type": "integer"
                },
                "Numerator": {
                    "type": "integer"
                },
                "Price/Dividend Adjustment": {
                    "type": "number"
                },
                "Volume Adjustment": {
                    "type": "number"
                }
            },
            "required": [
                "Denominator",
                "Numerator",
                "Price/Dividend Adjustment",
                "Volume Adjustment"
            ]
        }
        with self.assertRaises(SymbolNotFoundError):
            splits = self.adjustments.splits(TEST_SYMBOL_FAKE)
        splits = self.adjustments.splits(TEST_SYMBOL_NODIVSPLIT)
        self.assertIsNone(splits)
        price_collection = 'price.' + TEST_SYMBOL_DIVSPLIT
        collection = self.mongo_data.db[price_collection]
        initial_split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0, 'Interval': 0 })
        splits = self.adjustments.splits(TEST_SYMBOL_DIVSPLIT,regen=True)
        last_split_date = None
        for split_date in splits:
            validate(instance=splits[split_date],schema=split_schema)
            if last_split_date is not None:
                self.assertLess(split_date,last_split_date)
            last_split_date = split_date
        first_regen_split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0, 'Interval': 0 })
        if initial_split_data is not None:
            self.assertGreater(first_regen_split_data['Time'],initial_split_data['Time'])
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
        price_collection = 'price.' + TEST_SYMBOL_DIVSPLIT
        collection = self.mongo_data.db[price_collection]
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT)
        first_date = list(quotes)[0]
        init_quote_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0, 'Quotes': 0 })
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,regen=True)
        regen_quote_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0, 'Quotes': 0 })
        self.assertGreater(regen_quote_data['Time'],init_quote_data['Time'])
        with self.assertRaises(Exception):
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date='2022-02-29')
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,end_date='2022-02-29')
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date='BADLYFORMATTEDDATE')
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,end_date='BADLYFORMATTEDDATE')
        with self.assertRaises(Exception):
            tomorrow = str(date.today() + timedelta(days=1))
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=tomorrow)
        a_while_ago = str(date.today() - timedelta(days=90))
        today = str(date.today())
        with self.assertRaises(Exception):
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=today,end_date=a_while_ago)
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='BADPERIOD')
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='1Y',start_date=a_while_ago)
            quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,period='1Y',end_date=a_while_ago)
        quotes = self.daily.quote(TEST_SYMBOL_DIVSPLIT,start_date=a_while_ago,end_date=today)
        curr_range_date = None
        for range_date in quotes:
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
            past_period = int(re.sub(r"[Y]", "", period))
            now = dt.now().astimezone()
            max_past_date = "%d-%02d-%02d" % (now.year - int(past_period),now.month,1)
            quotes = self.monthly.quote(TEST_SYMBOL_DIVSPLIT,period)
            first_period_date = list(quotes)[0]
            self.assertLessEqual(first_date,first_period_date)
            self.assertLessEqual(max_past_date,first_period_date)

    def test_latest(self):
        return #ALEX
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.monthly.quote(TEST_SYMBOL_FAKE)
        with open(LATEST_PRICE_SCHEMA_FILE) as schema_file:
            validation_schema = json.load(schema_file)
        quote = self.latest.quote(TEST_SYMBOL_DIV)
        quoteTimeLong = int(time.time() * 1000)
        symbol = TEST_SYMBOL_DIV.upper()
        self.assertTrue('quotes' in quote)
        self.assertFalse('unknown_symbols' in quote)
        self.assertTrue(symbol in quote['quotes'])
        self.assertEqual(quote['quotes'][symbol]['symbol'], symbol)
        validate(instance=quote['quotes'][symbol],schema=validation_schema)
        self.assertEqual(quote['quotes'][symbol]['exchange'], TEST_SYMBOL_DIV_QUOTE_EXCHANGE)
        self.assertEqual(quote['quotes'][symbol]['exchangeName'], TEST_SYMBOL_DIV_QUOTE_EXCHANGE_NAME)
        self.assertGreaterEqual(quote['quotes'][symbol]['askPrice'],quote['quotes'][symbol]['bidPrice'])
        self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['lowPrice'])
        self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['openPrice'])
        self.assertLessEqual(quote['quotes'][symbol]['lowPrice'],quote['quotes'][symbol]['openPrice'])
        self.assertGreaterEqual(quoteTimeLong,quote['quotes'][symbol]['quoteTimeInLong'])
        self.assertGreaterEqual(quoteTimeLong,quote['quotes'][symbol]['tradeTimeInLong'])
        self.assertGreaterEqual(quoteTimeLong,quote['quotes'][symbol]['regularMarketTradeTimeInLong'])
        self.assertGreaterEqual(quote['quotes'][symbol]['tradeTimeInLong'],quote['quotes'][symbol]['regularMarketTradeTimeInLong'])
        self.assertLessEqual(abs(round(quote['quotes'][symbol]['netChange'] - (quote['quotes'][symbol]['lastPrice'] - quote['quotes'][symbol]['closePrice']),2)), .01)
        quote = self.latest.quote([TEST_SYMBOL_DIV.lower(),TEST_SYMBOL_DIVSPLIT,TEST_SYMBOL_FAKE.lower()])
        quoteTimeLong = int(time.time() * 1000)
        self.assertTrue('quotes' in quote)
        self.assertTrue('unknown_symbols' in quote)
        self.assertTrue(TEST_SYMBOL_FAKE.upper() in quote['unknown_symbols'])
        for symbol in [TEST_SYMBOL_DIV.upper(),TEST_SYMBOL_DIVSPLIT.upper()]:
            self.assertTrue(symbol in quote['quotes'])
            self.assertEqual(quote['quotes'][symbol]['symbol'], symbol)
            validate(instance=quote['quotes'][symbol],schema=validation_schema)
            if symbol == TEST_SYMBOL_DIV.upper():
                self.assertEqual(quote['quotes'][symbol]['exchange'], TEST_SYMBOL_DIV_QUOTE_EXCHANGE)
                self.assertEqual(quote['quotes'][symbol]['exchangeName'], TEST_SYMBOL_DIV_QUOTE_EXCHANGE_NAME)
            else:
                self.assertEqual(quote['quotes'][symbol]['exchange'], TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE)
                self.assertEqual(quote['quotes'][symbol]['exchangeName'], TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE_NAME)
            self.assertGreaterEqual(quote['quotes'][symbol]['askPrice'],quote['quotes'][symbol]['bidPrice'])
            self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['lowPrice'])
            self.assertGreaterEqual(quote['quotes'][symbol]['highPrice'],quote['quotes'][symbol]['openPrice'])
            self.assertLessEqual(quote['quotes'][symbol]['lowPrice'],quote['quotes'][symbol]['openPrice'])
            self.assertGreaterEqual(quoteTimeLong,quote['quotes'][symbol]['quoteTimeInLong'])
            self.assertGreaterEqual(quoteTimeLong,quote['quotes'][symbol]['tradeTimeInLong'])
            self.assertGreaterEqual(quoteTimeLong,quote['quotes'][symbol]['regularMarketTradeTimeInLong'])
            self.assertGreaterEqual(quote['quotes'][symbol]['tradeTimeInLong'],quote['quotes'][symbol]['regularMarketTradeTimeInLong'])
            self.assertLessEqual(abs(round(quote['quotes'][symbol]['netChange'] - (quote['quotes'][symbol]['lastPrice'] - quote['quotes'][symbol]['closePrice']),2)), .01)
        quote = self.latest.quote([TEST_SYMBOL_FAKE,TEST_SYMBOL_FAKE_TWO.lower()])
        self.assertFalse('quotes' in quote)
        self.assertTrue('unknown_symbols' in quote)
        self.assertTrue(TEST_SYMBOL_FAKE.upper() in quote['unknown_symbols'])
        self.assertTrue(TEST_SYMBOL_FAKE_TWO.upper() in quote['unknown_symbols'])

    def test_intraday(self):
        date_verifier = DateVerifier()
        two_days_ago = (dt.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        yesterday = (dt.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        '''
        with self.assertRaises(SymbolNotFoundError):
            quotes = self.monthly.quote(TEST_SYMBOL_FAKE)
        bad_min_frequency = min(VALID_INTRADAY_FREQUENCIES.keys()) - 1
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_DIV,frequency=bad_min_frequency)
        bad_max_frequency = max(VALID_INTRADAY_FREQUENCIES.keys()) + 1
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_DIV,frequency=bad_max_frequency)
        bad_min_period = min(VALID_INTRADAY_PERIODS) - 1
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_DIV,period=bad_min_period)
        bad_max_period = max(VALID_INTRADAY_PERIODS) + 1
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_DIV,period=bad_max_period)
        # The next two series use the default values for period and frequency
        quotes = self.intraday.quote(TEST_SYMBOL_DIV)
        self.assertEqual(DEFAULT_INTRADAY_PERIOD,len(quotes.keys()))
        for quote_date in quotes:
            date_verifier.verify_date(quote_date)
            last_quote_time = None
            for quote_time in quotes[quote_date]:
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
        # Check all period/frequency combinations
        for period in VALID_INTRADAY_PERIODS:
            with self.assertRaises(Exception):
                # period and start_date don't mix
                quotes = self.intraday.quote(TEST_SYMBOL_DIVSPLIT,period=period,start_date=two_days_ago)
            for frequency in VALID_INTRADAY_FREQUENCIES:
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
        # Various checks for absolute and relative dates
        too_old_date = (dt.strptime(OLDEST_QUOTE_DATE, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,start_date=too_old_date)
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=too_old_date)
        tomorrow = (dt.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,start_date=tommorow)
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=tomorrow)
        with self.assertRaises(Exception):
            quotes = self.intraday.quote(TEST_SYMBOL_SPLIT,end_date=two_days_ago,start_date=yesterday)
        '''
        for frequency in VALID_INTRADAY_FREQUENCIES:
            print(frequency)
            print(VALID_INTRADAY_FREQUENCIES[frequency])
        #ALEXHERE
        #with self.assertRaises(Exception):
        #    quotes = self.intraday.quote(TEST_SYMBOL_DIV,start_date='2000-01-05')
        #VALID_INTRADAY_FREQUENCIES = {1:50, 5:260, 10:260, 15:260, 30:260}
        #if start_date < oldest_available_date:
        #    raise Exception('For a minute frequency of ' + str(frequency) + ', the oldest available date is ' + oldest_available_date + '.')
        #if end_date < oldest_available_date:
        #    raise Exception('For a minute frequency of ' + str(frequency) + ', the oldest available date is ' + oldest_available_date + '.')
        #raise Exception('Cannot retrieve data for requested end date ' + end_date + ' and period ' + str(period) + ' since oldest available date is ' + oldest_available_date + '.')
        #print(json.dumps(quotes, indent=4))

if __name__ == '__main__':
    if len(sys.argv) == 2:
        unittest.main(argv=['run_username'])
    else:
        unittest.main()
