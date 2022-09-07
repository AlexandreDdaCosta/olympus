import collections, datetime, json, os, re, shutil, subprocess, time, urllib.request, wget

from datetime import date, timedelta, timezone
from datetime import datetime as dt
from dateutil.parser import parse
from file_read_backwards import FileReadBackwards

import olympus.securities.equities.data as data
import olympus.securities.equities.data.alphavantage as alphavantage
import olympus.securities.equities.data.tdameritrade as ameritrade
import olympus.securities.equities.data.symbols as symbols

from olympus import USER, User
from olympus.securities.equities.data.datetime import QUOTE_DATE_FORMAT, TradingDates

DEFAULT_INTRADAY_FREQUENCY = 30
MAP_LATEST_PRICE_KEYS = {
    "Open": "openPrice",
    "High": "highPrice",
    "Low": "lowPrice", 
    "Close": "closePrice", 
    "Volume": "totalVolume",
    "Adjusted Open": "openPrice",
    "Adjusted High": "highPrice",
    "Adjusted Low": "lowPrice",
    "Adjusted Close": "closePrice",
    "Adjusted Volume": "totalVolume"
    }
STORED_DIVIDEND_FORMAT = [ "Dividend", "Adjusted Dividend" ]
STORED_PRICE_FORMAT = [ "Open", "High", "Low", "Close", "Volume", "Adjusted Open", "Adjusted High", "Adjusted Low", "Adjusted Close", "Adjusted Volume" ]
STORED_SPLIT_FORMAT = [ "Numerator", "Denominator", "Price/Dividend Adjustment", "Volume Adjustment" ]
VALID_DAILY_WEEKLY_PERIODS = {'1M':30,'3M':91,'6M':183,'1Y':365,'2Y':730,'5Y':1825,'10Y':3652,'20Y':7305,'All':None}
VALID_INTRADAY_PERIODS = [1, 2, 3, 4, 5, 10]
VALID_INTRADAY_FREQUENCIES = {1:35, 5:180, 10:180, 15:180, 30:180}
# Keys: Frequency of quote (in minutes)
# Values: Number of trading days into the past from today for which data is available for given frequency
VALID_MONTHLY_PERIODS = ['1Y','2Y','5Y','10Y','20Y','All']

'''
When stored in the database, price data is split into separate collection by symbol
with the naming convention "price.<symbol>". The order of the documents stored within each collection
will vary, but the documents themselves can include the following:

Splits:

{
    "_id" : ObjectId("################"),
    "Time" : "<Last update time>",
    "Adjustment": "Splits",
    "Start Time": "<Time stamp for start of split records. One minute resolution.>",
    "End Time": "<Time stamp for end of split records. One minute resolution.>",
    "Splits" : {
        "<Time stamp, one minute resolution>" : {
            "Numerator" : <integer>,
            "Denominator" : <integer>,
            "Price/Dividend Adjustment" : <float>,
            "Volume Adjustment" : <float>
        },
        <more splits>
    }
}

Dividends:

{
    "_id" : ObjectId("################"),
    "Time" : "<Last update time>",
    "Adjustment": "Dividends",
    "Start Time": "<Time stamp for start of dividend records. One minute resolution.>",
    "End Time": "<Time stamp for end of dividend records. One minute resolution.>",
    "Dividends" : {
        "<Time stamp, one minute resolution>" : {
            "Dividend" : <float>[,
            "Adjusted Dividend" : <float>]
        },
        <more dividends>
    }
}

Date-merged splits and dividends:

{
    "_id" : ObjectId("################"),
    "Time" : "<Last update time>",
	"Adjustment" : "Merged",
	"Time Dividends" : "<Dividend update time for this record>",
	"Time Splits" : "<SPlit update time for this record>",
	"Adjustments" : {
        "<Time stamp, one minute resolution>" : {
			["Price Adjustment" : <integer>,
			"Volume Adjustment" : <float>][,]
			["Dividend" : <float>]
        },
        <more adjustments>
    }
}

Price quotes:

{
    "_id" : ObjectId("################"),
    "Time" : "<Last update time>",
    "Interval": "<Interval of series. Available: 1m/60m (minutes), 1d (day)>",
    "Start Time": "<Time stamp for first interval stored. One minute resolution.>",
    "End Time": "<Time stamp for last interval stored. One minute resolution.>",
    "Quotes" : {
        "<Time stamp, one minute resolution>" : {
            "Open" : "<quote>",
            "High" : "<quote>",
            "Low" : "<quote>",
            "Close" : "<quote>",
            "Volume" : "<integer>",
            "Adjusted Close" : "<quote>",
            [
            "Adjusted Open" : "<quote>",
            "Adjusted High" : "<quote>",
            "Adjusted Low" : "<quote>",
            "Adjusted Volume" : "<integer>",
            ]
        },
        <more quotes>
    }
}

Notes:

1. Unless so labeled, price and volume data are "as traded".
2. Adjustments are stored to facilitate the most common use case. Data sources are adjusted for
   splits, so adjustments are principally set up to UNDO data sources adjustments to retrieve as-traded
   prices, dividends, and volumes.
3. Split adjustments are cumulative, starting from the most recent date and extended into the past
   to the first recorded split. This allows for simple calculations when doing related price, volume,
   and dividend adjustments. Note that price and dividend adjustments are identical. Also note
   that adjustments begin on the date they are recorded.
4. Adjusted dividend numbers are included only when adjusted for splits.
5. Adjusted price figures within brackets are included only when they differ from as-traded numbers.
6. Merged adjustment data in brackets for a specific date will only appear when such data exists for
   that specific date.
7. Split ("Splits"), dividend ("Dividends"), and merged ("Adjustments") data will be null (None) when
   no data exists.

'''

class Adjustments(data.Connection):
    '''
Yahoo! Finance historical quotes are the data source for split and dividend history due to the data
being free and having a deep history.

DIVIDENDS
---------

Yahoo! Finance records split-adjusted dividends. It's therefore necessary to get split information
before dividend data in order to calculate the original value of recorded dividends. 

SPLITS
------

Splits are stored as separate numerator and denominator entries. As an example:

A "four-for-one" split is received as:

4:1

The left hand digit is the "numerator", and the right hand is the "denominator".

These entries are then used to calculate numbers used to adjust past as-traded price and volume data as
well as past issued dividends. Calculations begin with the most recent split, such that:

denominator / numerator is the calculation used to adjust price quotes and dividends for all dates prior
to the split date, up to the next oldest split date.
numerator / denominator is the calculation used to adjust volume numbers for all dates prior
to the split date, up to the next oldest split date.

For splits before the most recent one, the calculation must be multiplied by the matching figures for the 
next most recent split date to arrive at a CUMULATIVE adjustment.

For regular splits, this procedure results in past price and dividend data being adjusted DOWNWARD,
whereas past volume data will be adjusted UPWARD. The opposite is true in the case of a reverse split.

The dates stored imply the following logic: Use the calculated adjustments to adjust all historical
data UP TO the date of the split but not past the date of the next oldest recorded split. Data from a 
date more recent than or matching the date of the most recent split is therefore NEVER adjusted.
'''

    def __init__(self,username=USER,**kwargs):
        super(Adjustments,self).__init__(username,**kwargs)
        self.symbol_reader = symbols.Read(username,**kwargs)
        self.adjustment_dividend_date = None
        self.adjustment_split_date = None
        self.adjusted_symbol = None
        self.adjustment_data = None
        self.split_adjusted_symbol = None
        self.split_data_date = None

    def adjustments(self,symbol,**kwargs):
        # Returns all split and dividend adjustments for an equity's as-traded prices.
        # Adjustments are returned as a date-ordered array, with the most recent date first.
        symbol = str(symbol).upper()
        symbol_verify = kwargs.get('symbol_verify',True)
        if symbol_verify is True:
            symbol_data = self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        adjustments_collection = 'price.' + symbol
        collection = self.db[adjustments_collection]
        adjustments_data = collection.find_one({ 'Adjustment': 'Merged' },{ '_id': 0 })
        if adjustments_data is None:
            regen = True
        if regen is True or self._is_stale_data(adjustments_data['Time Dividends']) or self._is_stale_data(adjustments_data['Time Splits']):
            (splits_data,splits_date) = self.splits(symbol,return_date=True,**kwargs)
            (dividends_data,dividends_date) = self.dividends(symbol,return_date=True,**kwargs) 
            adjustments = []
            if splits_data is not None:
                split_entries = list(splits_data.items())
                split_count = len(split_entries)
                split_index = 0
            if dividends_data is not None:
                for dividend_date, dividend_dict in dividends_data.items():
                    dividend_adjustment = dividend_dict['Adjusted Dividend']
                    if splits_data is not None and split_index < split_count:
                        loop_index = split_index
                        dividend_written = False
                        for index in range(loop_index, split_count):
                            split_date = split_entries[index][0]
                            split_dict = split_entries[index][1]
                            if dividend_date > split_date:
                                adjustments.append({ 'Date': dividend_date, 'Dividend': dividend_adjustment })
                                dividend_written = True
                                break
                            elif dividend_date == split_date:
                                adjustments.append({ 'Date': dividend_date, 'Dividend': dividend_adjustment, 'Price Adjustment': split_dict['Price/Dividend Adjustment'], 'Volume Adjustment': split_dict['Volume Adjustment'] })
                                split_index = split_index + 1
                                dividend_written = True
                                break
                            else: # dividend_date < split_date
                                adjustments.append({ 'Date': split_date, 'Price Adjustment': split_dict['Price/Dividend Adjustment'], 'Volume Adjustment': split_dict['Volume Adjustment'] })
                                split_index = split_index + 1
                        if dividend_written is False:
                            adjustments.append({ 'Date': dividend_date, 'Dividend': dividend_adjustment })
                    else:
                        adjustments.append({ 'Date': dividend_date, 'Dividend': dividend_adjustment })
            if splits_data is not None:
                for index in range(split_index, split_count):
                    split_date = split_entries[split_index][0]
                    split_dict = split_entries[split_index][1]
                    adjustments.append({ 'Date': split_date, 'Price Adjustment': split_dict['Price/Dividend Adjustment'], 'Volume Adjustment': split_dict['Volume Adjustment'] })
            if len(adjustments) == 0:
                adjustments = None
            write_dict = {}
            write_dict['Time'] = str(dt.now().astimezone())
            write_dict['Adjustment'] = 'Merged'
            write_dict['Time Dividends'] = dividends_date
            write_dict['Time Splits'] = splits_date
            write_dict['Adjustments'] = adjustments
            collection.delete_many({ 'Adjustment': 'Merged' })
            collection.insert_one(write_dict)
            return adjustments
        else:
            return adjustments_data['Adjustments']

    def dividends(self,symbol,**kwargs):
        symbol = str(symbol).upper()
        symbol_verify = kwargs.get('symbol_verify',True)
        if symbol_verify is True:
            symbol_data = self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        return_date = kwargs.get('return_date',False)
        dividend_collection = 'price.' + symbol
        target_file = self.download_directory()+symbol+'-dividends.csv'
        collection = self.db[dividend_collection]
        dividend_data = collection.find_one({ 'Adjustment': 'Dividends' },{ '_id': 0 })
        query_date = None
        stale = False
        start_dividend_date = None
        end_dividend_date = None
        if dividend_data is not None:
            start_dividend_date = dividend_data['Start Date']
            end_dividend_date = dividend_data['End Date']
            query_date = dividend_data['Time']
        if regen is False and dividend_data is not None:
            stale = self._is_stale_data(dividend_data['Time'])
        elif dividend_data is None:
            regen = True
        returndata = None
        if stale is True or regen is True:
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=0&period2=9999999999&events=div'
            response = urllib.request.urlretrieve(url,target_file)
            json_dividends = None
            with open(target_file,'r') as f:
                if not re.match(r'^Date,Dividends',f.readline()):
                    raise Exception('First line of symbol dividend data .csv file does not match expected format.')
                for line in f:
                    json_dividend = []
                    line = line.rstrip()
                    pieces = line.rstrip().split(',')
                    dividend_date = pieces[0]
                    adjusted_dividend = float(pieces[1])
                    if (start_dividend_date is None or start_dividend_date >= dividend_date):
                        start_dividend_date = dividend_date
                    if (end_dividend_date is None or end_dividend_date <= dividend_date):
                        end_dividend_date = dividend_date
                    # Here we have the dividend adjusted for any subsequent or concurrent splits.
                    # Determine the unadjusted value, and store that.
                    # If the adjusted value is different, store that as well.
                    adjustment_factors = self.split_adjustment(symbol,dividend_date,regen=regen,symbol_verify=False)
                    if adjustment_factors is not None:
                        # Use the reciprocal of the price/dividend adjustment to undo the split adjustment on the dividend
                        json_dividend.append(round(float(adjustment_factors['Price/Dividend Adjustment']) * adjusted_dividend,2))
                    json_dividend.append(adjusted_dividend)
                    if json_dividends is None:
                        json_dividends = {}
                    json_dividends[dividend_date] = json_dividend
                write_dict = {}
                write_dict['Time'] = str(dt.now().astimezone())
                write_dict['Adjustment'] = 'Dividends'
                write_dict['Format'] = STORED_DIVIDEND_FORMAT
                write_dict['Start Date'] = start_dividend_date
                write_dict['End Date'] = end_dividend_date
                write_dict['Dividends'] = json_dividends
                collection.delete_many({ 'Adjustment': 'Dividends' })
                collection.insert_one(write_dict)
                query_date = write_dict['Time']
                returndata = write_dict['Dividends']
            os.remove(target_file)

        if returndata is None and dividend_data is not None:
            returndata = dividend_data['Dividends']
        # Format returned data using data headers
        formatted_returndata = {}
        details_length = len(STORED_DIVIDEND_FORMAT)
        if returndata is not None:
            for dividend_date in returndata:
                formatted_returndata[dividend_date] = {}
                dividend_length = len(returndata[dividend_date])
                for index in range(0, details_length):
                    if index >= dividend_length:
                        formatted_returndata[dividend_date][STORED_DIVIDEND_FORMAT[index]] = returndata[dividend_date][index-1]
                    else:
                        formatted_returndata[dividend_date][STORED_DIVIDEND_FORMAT[index]] = returndata[dividend_date][index]
            if return_date is False:
                return collections.OrderedDict(sorted(formatted_returndata.items(),reverse=True))
            else:
                return (collections.OrderedDict(sorted(formatted_returndata.items(),reverse=True)),query_date)
        if return_date is False:
            return None
        else:
            return (None,query_date)

    def splits(self,symbol,**kwargs):
        symbol = str(symbol).upper()
        symbol_verify = kwargs.get('symbol_verify',True)
        if symbol_verify is True:
            symbol_data = self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        return_date = kwargs.get('return_date',False)
        split_collection = 'price.' + symbol
        target_file = self.download_directory()+symbol+'-splits.csv'
        collection = self.db[split_collection]
        split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0 })
        query_date = None
        stale = False
        start_split_date = None
        end_split_date = None
        if split_data is not None:
            query_date = split_data['Time']
            start_split_date = split_data['Start Date']
            end_split_date = split_data['End Date']
        if regen is False and split_data is not None:
            stale = self._is_stale_data(split_data['Time'])
        elif split_data is None:
            regen = True
        returndata = None
        if stale is True or regen is True:
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=0&period2=9999999999&events=split'
            response = urllib.request.urlretrieve(url,target_file)
            splits = {}
            with open(target_file,'r') as f:
                if not re.match(r'^Date,Stock Splits',f.readline()):
                    raise Exception('First line of symbol split data .csv file does not match expected format.')
                for line in f:
                    line = line.rstrip()
                    pieces = line.rstrip().split(',')
                    splits[str(pieces[0])] = str(pieces[1])
            json_splits = None
            last_split = None
            for split_date in sorted(splits.keys(),reverse=True):
                json_split = []
                if (start_split_date is None or start_split_date >= split_date):
                    start_split_date = split_date
                if (end_split_date is None or end_split_date <= split_date):
                    end_split_date = split_date
                (numerator,denominator) = splits[split_date].rstrip().split(':')
                json_split.append(int(numerator))
                json_split.append(int(denominator))
                numerator = float(numerator)
                denominator = float(denominator)
                price_dividend_adjustment = (numerator/denominator)
                volume_adjustment = (denominator/numerator)
                if last_split is not None:
                    price_dividend_adjustment = price_dividend_adjustment * float(last_split[2])
                    volume_adjustment = volume_adjustment * float(last_split[3])
                json_split.append(price_dividend_adjustment)
                json_split.append(volume_adjustment)
                last_split = json_split
                if json_splits is None:
                    json_splits = {}
                json_splits[split_date] = json_split
            write_dict = {}
            write_dict['Time'] = str(dt.now().astimezone())
            write_dict['Adjustment'] = 'Splits'
            write_dict['Format'] = STORED_SPLIT_FORMAT
            write_dict['Start Date'] = start_split_date
            write_dict['End Date'] = end_split_date
            write_dict['Splits'] = json_splits
            collection.delete_many({ 'Adjustment': 'Splits' })
            collection.insert_one(write_dict)
            query_date = write_dict['Time']
            returndata = write_dict['Splits']
            os.remove(target_file)

        if returndata is None and split_data is not None:
            returndata = split_data['Splits']
        # Format returned data using data headers
        formatted_returndata = {}
        details_length = len(STORED_SPLIT_FORMAT)
        if returndata is not None:
            for quote_date in returndata:
                formatted_returndata[quote_date] = {}
                quote_length = len(returndata[quote_date])
                for index in range(0, details_length):
                    formatted_returndata[quote_date][STORED_SPLIT_FORMAT[index]] = returndata[quote_date][index]
            if return_date is False:
                return collections.OrderedDict(sorted(formatted_returndata.items(),reverse=True))
            else:
                return (collections.OrderedDict(sorted(formatted_returndata.items(),reverse=True)),query_date)
        if return_date is False:
            return None
        else:
            return (None,query_date)

    def split_adjustment(self,symbol,value_date,**kwargs):
        # Returns split adjustment values for unadjusted prices on a given date
        symbol = str(symbol).upper()
        if self.split_adjusted_symbol is None or self.split_adjusted_symbol != symbol or self.split_data_date is None or self._is_stale_data(self.split_data_date):
            (self.split_adjustment_data,self.split_data_date) = self.splits(symbol,return_date=True,**kwargs) 
            self.split_adjusted_symbol = symbol
        if self.split_adjustment_data is not None:
            for adjustment_date in reversed(self.split_adjustment_data):
                if value_date < adjustment_date:
                    return(self.split_adjustment_data[adjustment_date])
        return None

    def _is_stale_data(self,refresh_date):
        # These rules are designed to exclude quotes for the ongoing trading day,
        # since these quotes are constantly changing and will introduce anomalies
        # into saved data.
        # 9 PM is chosen as that is an hour past the close of extended hours trading.
        # Query source:
        # If now is a weekday and before 9:00 PM, generated before 9:00 PM yesterday
        # If now is a weekday and after 9:00 PM, generated before 9:00 PM today
        # If now is a weekend day, generated before 9:00 last Friday
        stale = False
        refresh_date_object = parse(refresh_date)
        now = dt.now().astimezone()
        time_zone_offset_string = str(now)[-5:]
        weekday_no = now.weekday()
        yesterday = now - timedelta(days = 1)
        if weekday_no < 5:
            # Weekday
            nine_pm_yesterday = "%d-%02d-%02d 21:00:00.000000-" % (yesterday.year,yesterday.month,yesterday.day) + time_zone_offset_string
            nine_pm_yesterday_object = parse(nine_pm_yesterday)
            nine_pm = "%d-%02d-%02d 21:00:00.000000-" % (now.year,now.month,now.day) + time_zone_offset_string
            nine_pm_object = parse(nine_pm)
            if now <= nine_pm_object and refresh_date_object < nine_pm_yesterday_object:
                stale = True
            elif now > nine_pm_object and refresh_date_object < nine_pm_object:
                stale = True
        else:
            # Weekend
            last_friday = now - timedelta(days=(weekday_no-4))
            last_friday_string = "%d-%02d-%02d 21:00:00.000000-04:00" % (last_friday.year,last_friday.month,last_friday.day)
            last_friday_object = parse(last_friday_string)
            if refresh_date_object < last_friday_object:
                stale = True
        return stale

class Daily(Adjustments):
    '''
Yahoo! Finance historical quotes are the data source for daily prices.

This was done for the following considerations:

1. Free
2. No known download limits
3. Long-term data available

Peculiarities:

1. Prices are all adjusted. Yahoo!'s plain "Open/High/Low/Close/Volume" figures are adjusted for stock splits only.
2. Based on the formatting of the price data, daily data is therefore saved as follows:
   a. Maintain up-to-date records of a symbol's historical price splits and dividends, also available for download
      from Yahoo! Finance historical quotes. These records include "Price/Dividend Adjustment" and
      "Volume Adjustment" factors.
   b. To derive as-traded prices and volume, take "Open/High/Low/Close/Volume" and multiply by the reciprocal
      of the split adjustment factor.
   c. To derive split- and dividend-adjusted prices, start with as-traded data. Then apply:
      (1) Split adjustment
      (2) Split-adjusted dividend adjustment (for prices only)
      Apply these adjustments for each date sequentially. For efficiency, start with the most recent as-traded
      data along with the most recent adjustment data and work backwards simultaneously with both data sets

I have confirmed that procedure generates price and volume data that tolerably match across a number of different
stock price and volume quoting services:

Yahoo! Finance
TD Ameritrade
AlphaVantage
stockcharts.com
tradingview.com
investors.com
msn.com
Google Finance
barchart.com

There are still minor differences between the data returned by different services, partly accounted for by the
following factors:

1. Yahoo! Finance rounds volume numbers to the nearest hundred.
2. Different services that give adjusted prices appear to use slightly different interpretations of the adjustment
   methodology given by the Center for Research in Security Prices (CRSP).

But since stored data is compared against other data that has been adjusted according to the same methodology,
my current judgment is that these differences will not grossly affect the desired results.

'''

    def __init__(self,username=USER,**kwargs):
        super(Daily,self).__init__(username,**kwargs)

    def quote(self,symbol,**kwargs):
        symbol = str(symbol).upper()
        symbol_data = self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        if regen is True:
            regen_adjustments = True
        else:
            regen_adjustments = False
        period = kwargs.get('period',None)
        start_date = kwargs.get('start_date',None)
        end_date = kwargs.get('end_date',None)
        self.today = str(date.today())
        if period is not None:
            if start_date is not None or end_date is not None:
                raise Exception('Cannot specify both a time period and a start/end date.')
            start_date = self._verify_period(period)
        if start_date is not None:
            dt.strptime(start_date, QUOTE_DATE_FORMAT) # Date verification
            if start_date >= self.today:
                raise Exception('Requested start date in not in the past.')
            if end_date is not None and end_date <= start_date:
                raise Exception('Requested start date is not older than requested end date.')
        if end_date is not None:
            dt.strptime(end_date, QUOTE_DATE_FORMAT) # Date verification
            if end_date > self.today:
                raise Exception('Requested end date in the future.')
        now = dt.now().astimezone()
        price_collection = 'price.' + symbol
        returndata = None
        target_file = self.download_directory()+symbol+'-daily.csv'

        # First we check/update stored data to save on bandwidth
        collection = self.db[price_collection]
        interval_data = collection.find_one({ 'Interval': '1d' },{ '_id': 0, 'Interval': 0 })
        stale = False
        self.start_date_daily = None
        self.end_date_daily = None
        self.cutoff_today = False
        time_zone_offset_string = str(now)[-5:]
        nine_pm_today = "%d-%02d-%02d 21:00:00.000000-" % (now.year,now.month,now.day) + time_zone_offset_string
        nine_pm_object = parse(nine_pm_today)
        if now < nine_pm_object:
            self.cutoff_today = True

        if interval_data is not None:
            self.start_date_daily = interval_data['Start Date']
            self.end_date_daily = interval_data['End Date']
        if regen is False and interval_data is not None:
            stale = self._is_stale_data(interval_data['Time'])
        elif interval_data is None:
            regen = True
        if regen is False and stale is True:
            if self.end_date_daily is not None:
                year,month,day = map(int,self.end_date_daily.rstrip().split('-'))
                period1 = str(int(dt(year, month, day, 0, 0, 0).timestamp()))
            url = self._daily_quote_url(symbol,period1)
            response = urllib.request.urlretrieve(url,target_file)
            with open(target_file,'r') as f:
                self._verify_csv_daily_format(f.readline())
                if self.end_date_daily is not None:
                    compare_line = f.readline().rstrip()
                    pieces = compare_line.rstrip().split(',')
                    if round(interval_data['Quotes'][self.end_date_daily][3],2) != round(float(pieces[5]),2):
                        # There's been a price adjustment, regenerate everything
                        regen = True
            if regen is False:
                adjustments = self._init_adjustments(symbol,regen_adjustments)
                subprocess.check_output("/usr/bin/sed -i '1d' " + target_file, shell=True)
                with FileReadBackwards(target_file, encoding="utf-8") as f:
                    for line in f:
                        (json_quote,interval_date) = self._parse_daily(line,adjustments)
                        if json_quote is not None:
                            collection.update_one({'Interval': '1d'},{ "$set": {'Quotes.'+interval_date: json_quote}}, upsert=True)
                            interval_data['Quotes'][interval_date] = json_quote
                    collection.update_one({'Interval': '1d'},{ "$set":  {'End Date': self.end_date_daily, 'Start Date': self.start_date_daily, 'Time': str(now)}})
            os.remove(target_file)
        if regen is True:
            adjustments = self._init_adjustments(symbol,regen_adjustments)
            url = self._daily_quote_url(symbol)
            response = urllib.request.urlretrieve(url,target_file)
            # The initial response contains split-only adjusted prices, ordered from oldest to newest.
            with open(target_file,'r') as f:
                self._verify_csv_daily_format(f.readline())
            # Remove the first line of the target file prior to reading price data in reverse.
            subprocess.check_output("/usr/bin/sed -i '1d' " + target_file, shell=True)
            # Read file line-by-line in reverse (newest to oldest), since adjustments occur from
            # the most recent data (always as-traded).
            with FileReadBackwards(target_file, encoding="utf-8") as f:
                json_quotes = {}
                for line in f:
                    (json_quote,interval_date) = self._parse_daily(line,adjustments)
                    if json_quote is not None:
                        json_quotes[interval_date] = json_quote
            write_dict = {}
            write_dict['Time'] = str(now)
            write_dict['Interval'] = '1d'
            write_dict['Format'] = STORED_PRICE_FORMAT
            write_dict['Start Date'] = self.start_date_daily
            write_dict['End Date'] = self.end_date_daily
            write_dict['Quotes'] = {key:json_quotes[key] for key in sorted(json_quotes)}
            collection.delete_many({ 'Interval': '1d' })
            collection.insert_one(write_dict)
            interval_data = write_dict
            returndata = write_dict['Quotes']
            os.remove(target_file)

        if returndata is None:
            returndata = interval_data['Quotes']
        # Trim data outside of requested date range
        if start_date is not None:
            start_date = dt.strptime(start_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") >= start_date}
        if end_date is not None:
            end_date = dt.strptime(end_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") <= end_date}
        # Format returned data using data headers
        formatted_returndata = {}
        details_length = len(STORED_PRICE_FORMAT)
        for quote_date in returndata:
            formatted_returndata[quote_date] = {}
            quote_length = len(returndata[quote_date])
            for index in range(0, details_length):
                if index >= quote_length:
                    formatted_returndata[quote_date][STORED_PRICE_FORMAT[index]] = returndata[quote_date][index-5]
                else:
                    formatted_returndata[quote_date][STORED_PRICE_FORMAT[index]] = returndata[quote_date][index]
        return collections.OrderedDict(sorted(formatted_returndata.items()))

    def _daily_quote_url(self,symbol,period1='0'):
        period2 = '9999999999' # To the present day, and beyooond
        return 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=' + period1 + '&period2=' + period2 + '&interval=1d&events=history'

    def _init_adjustments(self,symbol,regen):
        adjustments = self.adjustments(symbol,regen=regen,symbol_verify=False)
        if adjustments is not None:
            self.adjustments_length = len(adjustments)
            self.adjustments_index = 0
            self.next_adjustment = adjustments[self.adjustments_index]
            self.dividend_adjustment = 1.0
            self.price_adjustment = 1
            self.volume_adjustment = 1.0
        return adjustments

    def _parse_daily(self,line,adjustments):
        # Received data is split-adjusted only, excluding adjusted close. Therefore:
        # 1. Ignore the reported "Adjusted Close" in all lines (pieces[5])
        # 2. Remove split adjustments for price and volume to get as-traded prices and volumes
        # 3. Apply dividend adjustments to price to get split- and dvidend-adjusted prices.
        # 4. Use reported volume as adjusted volume.
        line = line.rstrip()
        pieces = line.rstrip().split(',')
        interval_date = str(pieces[0])
        if self.cutoff_today and interval_date == self.today:
            return None, None
        if (self.start_date_daily is None or self.start_date_daily >= interval_date):
            self.start_date_daily = interval_date
        if (self.end_date_daily is None or self.end_date_daily <= interval_date):
            self.end_date_daily = interval_date
        quote = []
        if adjustments is None:
            quote.append(round(float(pieces[1]),2)) # Open
            quote.append(round(float(pieces[2]),2)) # High
            quote.append(round(float(pieces[3]),2)) # Low
            quote.append(round(float(pieces[4]),2)) # Close
            quote.append(int(pieces[6])) # Volume
        else:
            if self.next_adjustment is not None and interval_date < self.next_adjustment['Date']:
                '''
                Dividend adjustments for dates prior to the ex-dividend date are done according to the following calculation:

                Closing price on day prior to dividend - dividend amount
                -------------------------------------------------------- = Adjustment factor
                       Closing price on day prior to dividend

                Multiply the adjustment factor by all prices before the ex-dividend date to calculate adjusted prices.

                In the common case of multiple historical dividends, the adjustment factors are CUMULATIVE, which means that
                the calculated adjustment factor for a specific date must be multiplied by all later adjustment factors
                to get the actual adjustment factor for that date. Therefore, calculating adjustments require that we know
                closing prices for the security.

                The data source gives us split-adjusted prices, which we rely on to calculate all other prices. Therefore,
                the above calculation uses the split-adjusted closing price and the split-adjusted dividend.

                '''
                if 'Dividend' in self.next_adjustment:
                    # Note that the data source extends to six decimal places
                    self.dividend_adjustment = self.dividend_adjustment * ((float(pieces[4]) - float(self.next_adjustment['Dividend'])) / float(pieces[4]))
                if 'Price Adjustment' in self.next_adjustment:
                    # These two always show up together (reciprocals)
                    self.price_adjustment = self.next_adjustment['Price Adjustment']
                    self.volume_adjustment = self.next_adjustment['Volume Adjustment']
                self.adjustments_index = self.adjustments_index + 1
                if self.adjustments_index < self.adjustments_length:
                    self.next_adjustment = adjustments[self.adjustments_index]
                else:
                    self.next_adjustment = None
            if self.dividend_adjustment == 1.0 and self.price_adjustment == 1:
                quote.append(round(float(pieces[1]),2)) # Open
                quote.append(round(float(pieces[2]),2)) # High
                quote.append(round(float(pieces[3]),2)) # Low
                quote.append(round(float(pieces[4]),2)) # Close
                quote.append(int(pieces[6])) # Volume
            else:
                quote.append(round(float(pieces[1]) * float(self.price_adjustment),2)) # Open
                quote.append(round(float(pieces[2]) * float(self.price_adjustment),2)) # High
                quote.append(round(float(pieces[3]) * float(self.price_adjustment),2)) # Low
                quote.append(round(float(pieces[4]) * float(self.price_adjustment),2)) # Close
                quote.append(int(int(pieces[6]) * float(self.volume_adjustment))) # Volume
                # Adjusted prices rounded to 6 places for better accuracy when plotting small adjusted numbers
                quote.append(round(float(pieces[1]) * self.dividend_adjustment,6)) # Adjusted open
                quote.append(round(float(pieces[2]) * self.dividend_adjustment,6)) # Adjusted high
                quote.append(round(float(pieces[3]) * self.dividend_adjustment,6)) # Adjusted low
                quote.append(round(float(pieces[5]),6)) # Adjusted close
                quote.append(int(pieces[6])) # Adjusted volume
        return (quote,interval_date)

    def _verify_csv_daily_format(self,first_line):
        if not re.match(r'^Date,Open,High,Low,Close,Adj Close,Volume',first_line):
            raise Exception('First line of symbol daily data .csv file does not match expected format.')

    def _verify_period(self,period):
        if period not in VALID_DAILY_WEEKLY_PERIODS.keys():
            raise Exception('Invalid period specified; must be one of the following: ' + ', ' . join(VALID_DAILY_WEEKLY_PERIODS))
        if VALID_DAILY_WEEKLY_PERIODS[period] is not None:
            start_date = str(date.today() - timedelta(days=VALID_DAILY_WEEKLY_PERIODS[period]))
        else:
            start_date = None
        return start_date

class Weekly(Daily):

    def __init__(self,username=USER,**kwargs):
        super(Weekly,self).__init__(username,**kwargs)
        self.merge = QuoteMerger()

    def quote(self,symbol,period='1Y',**kwargs):
        kwargs.pop('start_date',None)
        kwargs.pop('end_date',None)
        daily_quotes = super().quote(symbol,period=period,**kwargs)
        self.merge.reset_quote()
        last_day_of_week = None
        last_start_date_of_week = None
        weekly_quotes = {}
        for quote_date in daily_quotes:
            day_of_week = dt.strptime(quote_date,'%Y-%m-%d').isoweekday()
            if last_day_of_week is not None and day_of_week < last_day_of_week:
                quote = self.merge.set_quote()
                weekly_quotes[last_start_date_of_week] = quote
                last_start_date_of_week = quote_date
                self.merge.init_quote(daily_quotes[quote_date])
            else:
                if last_start_date_of_week is None:
                    last_start_date_of_week = quote_date
                self.merge.compare_quotes(daily_quotes[quote_date])
            last_day_of_week = day_of_week
        quote = self.merge.set_quote()
        weekly_quotes[last_start_date_of_week] = quote
        return weekly_quotes

    def _verify_period(self,period):
        start_date = super()._verify_period(period)
        if start_date is not None:
            day_of_week = dt.strptime(start_date,'%Y-%m-%d').isoweekday()
            if day_of_week != 1:
                start_date = str(dt.strptime(start_date,'%Y-%m-%d') - timedelta(days=(day_of_week-1)))[0:10]
        return start_date

class Monthly(Daily):

    def __init__(self,username=USER,**kwargs):
        super(Monthly,self).__init__(username,**kwargs)
        self.merge = QuoteMerger()

    def quote(self,symbol,period='5Y',**kwargs):
        kwargs.pop('start_date',None)
        kwargs.pop('end_date',None)
        start_date = self._verify_period(period)
        if start_date is not None:
            daily_quotes = super().quote(symbol,start_date=start_date,**kwargs)
        else:
            daily_quotes = super().quote(symbol,**kwargs)
        self.merge.reset_quote()
        last_start_date_of_month = None
        previous_month = None
        monthly_quotes = {}
        for quote_date in daily_quotes:
            month = quote_date[5:-3]
            year = quote_date[0:4]
            if previous_month is not None and month != previous_month:
                quote = self.merge.set_quote()
                monthly_quotes[last_start_date_of_month] = quote
                last_start_date_of_month = year + '-' + month + '-' + '01'
                self.merge.init_quote(daily_quotes[quote_date])
            else:
                if last_start_date_of_month is None:
                    last_start_date_of_month = year + '-' + month + '-' + '01'
                self.merge.compare_quotes(daily_quotes[quote_date])
            previous_month = month
        quote = self.merge.set_quote()
        monthly_quotes[last_start_date_of_month] = quote
        return monthly_quotes

    def _verify_period(self,period):
        if period not in VALID_MONTHLY_PERIODS:
            raise Exception('Invalid period specified; must be one of the following: ' + ', ' . join(VALID_MONTHLY_PERIODS))
        start_date = None
        if period != 'All':
            period = re.sub(r"[Y]", "", period) # All periods are in the form "#Y", with "Y" signifying years
            now = dt.now().astimezone()
            start_date = "%d-%02d-%02d" % (now.year - int(period),now.month,1)
        return start_date

class QuoteMerger():

    def __init__(self):
        pass

    def compare_quotes(self,quote):
        for item in ['Open','Adjusted Open']:
            if getattr(self, item) is None:
                setattr(self, item, quote[item])
        for item in ['High','Adjusted High']:
            if getattr(self, item) is None or quote[item] > getattr(self, item):
                setattr(self, item, quote[item])
        for item in ['Low','Adjusted Low']:
            if getattr(self, item) is None or quote[item] < getattr(self, item):
                setattr(self, item, quote[item])
        for item in ['Close','Adjusted Close']:
            setattr(self, item, quote[item])
        for item in ['Volume','Adjusted Volume']:
            setattr(self, item, getattr(self, item) + quote[item])

    def init_quote(self,quote):
        for label in STORED_PRICE_FORMAT:
            setattr(self, label, quote[label])

    def reset_quote(self):
        for label in STORED_PRICE_FORMAT:
            setattr(self, label, None)
        setattr(self, 'Adjusted Volume', 0)
        setattr(self, 'Volume', 0)

    def set_quote(self):
        quote = {}
        for label in STORED_PRICE_FORMAT:
            quote[label] = getattr(self, label)
        return quote

class Intraday(ameritrade.Connection):
    '''
This class focuses on the minute-by-minute price quotes available via the TD Ameritrade API.
    '''

    def __init__(self,username=USER,**kwargs):
        super(Intraday,self).__init__(username,**kwargs)
        self.symbol_reader = symbols.Read(username,**kwargs)

    def quote(self,symbol,frequency=30,**kwargs):
        symbol = str(symbol).upper()
        symbol_data = self.symbol_reader.get_symbol(symbol)
        self._verify_frequency(frequency)
        need_extended_hours_data = kwargs.get('need_extended_hours_data',True)
        period = kwargs.get('period',None)
        end_date = kwargs.get('end_date',None)
        start_date = kwargs.get('start_date',None)
        period = self._verify_period(period,start_date,end_date)
        params = { 'frequency': frequency, 'frequencyType': 'minute', 'needExtendedHoursData': need_extended_hours_data, 'periodType': 'day' }
        period = None #ALEX
        if period is not None:
            params['period'] = period
        start_date = '2021-12-16' #ALEX
        #end_date = '2022-09-06' #ALEX
        (start_date, end_date) = self._verify_dates(start_date,end_date,frequency)
        if start_date is not None:
            params['startDate'] = start_date
        if end_date is not None:
            params['endDate'] = end_date
        print(params) #ALEX
        response = self.request('marketdata/' + symbol + '/pricehistory',params)
        if response['symbol'] != symbol:
            raise Exception('Incorrect symbol ' + str(response['symbol']) + ' returned by API call.')
        for quote in response['candles']: #ALEX
            print(quote['datetime']) #ALEX
            print(dt.fromtimestamp(quote['datetime']/1000)) #ALEX
            print(quote) #ALEX
        return response

    def _verify_dates(self,start_date,end_date,frequency):
        if end_date is not None and start_date is None:
            raise Exception('Keyword end_date is defined; this requires keyword start_date to also be defined.')
        if start_date is not None:
            date_counter = TradingDates()
            trade_days = date_counter.trade_days(start_date,end_date)
            if trade_days > VALID_INTRADAY_FREQUENCIES[frequency]:
                raise Exception('Start date is too far in the past. For the given frequency of ' + str(frequency) + ' minutes, only ' + str(VALID_INTRADAY_FREQUENCIES[frequency]) + ' past trading days are available.')
            start_date = dt(int(start_date[:4]), int(start_date[-5:-3]), int(start_date[-2:]), 0, 0, 0).strftime('%s')
            start_date = int(start_date) * 1000 # Milliseconds per API
        if end_date is not None:
            end_date = dt(int(end_date[:4]), int(end_date[-5:-3]), int(end_date[-2:]), 0, 0, 0).strftime('%s')
            end_date = int(end_date) * 1000 # Milliseconds
        return start_date, end_date

    def _verify_frequency(self,frequency):
        if frequency not in VALID_INTRADAY_FREQUENCIES.keys():
            raise Exception('Invalid frequency specified; must be one of the following: ' + ', ' . join(VALID_INTRADAY_FREQUENCIES))

    def _verify_period(self,period,end_date,start_date):
        if period is not None and period not in VALID_INTRADAY_PERIODS:
            raise Exception('Invalid period specified; must be one of the following: ' + ', ' . join(VALID_INTRADAY_PERIODS))
        if period is not None and start_date is not None and end_date is not None:
            raise Exception('The keyword argument "period" cannot be declared with both the "end_date" and "start_date" keyword arguments.')
        if period is None and ((start_date is None and end_date is None) or (start_date is None and end_date is not None) or (start_date is not None and end_date is None)):
            period = 10 # Ameritrade default (ten days)
        return period

class Latest(ameritrade.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Latest,self).__init__(username,**kwargs)
        self.symbol_reader = symbols.Read(username,**kwargs)

    def quote(self,symbol,**kwargs):
        params = {}
        unknown_symbols = []
        unquoted_symbols = []
        # "Standardize" means to add keys corresponding to those appearing in STORED_PRICE_FORMAT
        standardize = kwargs.get('standardize',False)
        # Symbol can be a string or array (list of symbols)
        if isinstance(symbol,str):
            symbol = symbol.upper()
            try:
                symbol_data = self.symbol_reader.get_symbol(symbol)
            except symbols.SymbolNotFoundError:
                unknown_symbols.append(symbol)
                reply = { 'unknown_symbols': unknown_symbols }
                return reply
            except:
                raise
            params['symbol'] = symbol
        elif isinstance(symbol,list):
            symbol = [x.upper() for x in symbol]
            symbol_data = self.symbol_reader.get_symbols(symbol)
            unknown_symbols = symbol_data['unknownSymbols']
            quote_symbols = symbol_data['symbols'].keys()
            if (not quote_symbols):
                reply = { 'unknown_symbols': unknown_symbols }
                return reply
            params['symbol'] = ','.join(quote_symbols)
        response = self.request('v1/marketdata/quotes','GET',params,with_apikey=True)
        if isinstance(symbol,str):
            if symbol not in response and symbol not in unknown_symbols:
                unquoted_symbols.append(symbol)
        elif isinstance(symbol,list):
            for uc_symbol in symbol:
                if uc_symbol not in response and uc_symbol not in unknown_symbols:
                    unquoted_symbols.append(uc_symbol)
        for quote_symbol in response:
            response[quote_symbol]['date'] = dt.fromtimestamp(response[quote_symbol]['quoteTimeInLong'] / 1000).strftime('%Y-%m-%d')
            if standardize is True:
                for mapped_key in MAP_LATEST_PRICE_KEYS:
                    response[quote_symbol][mapped_key] = response[quote_symbol][MAP_LATEST_PRICE_KEYS[mapped_key]]
        reply = { 'quotes': response }
        if unknown_symbols:
            reply['unknown_symbols'] = unknown_symbols
        if unquoted_symbols:
            reply['unquoted_symbols'] = unquoted_symbols
        return reply
