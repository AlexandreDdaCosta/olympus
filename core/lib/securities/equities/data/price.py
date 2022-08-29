import collections, datetime, json, os, re, shutil, subprocess, time, urllib.request, wget

from datetime import date, timedelta
from datetime import datetime as dt
from dateutil.parser import parse
from file_read_backwards import FileReadBackwards

from olympus import USER, User

import olympus.securities.equities.data as data
import olympus.securities.equities.data.alphavantage as alphavantage
import olympus.securities.equities.data.tdameritrade as ameritrade
import olympus.securities.equities.data.symbols as symbols

DATE_FORMAT = "%Y-%m-%d"
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
VALID_DAILY_WEEKLY_PERIODS = ['1M','3M','6M','1Y','2Y','5Y','10Y','All']

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
        # Query source:
        # If now is a weekday and before 4:00 PM, generated before today
        # If now is a weekday and after 4:00 PM, generated before 4:00 PM today
        # If now is a weekend day, generated before 4:00 last Friday
        stale = False
        refresh_date_object = parse(refresh_date)
        now = dt.now().astimezone()
        weekday_no = now.weekday()
        if weekday_no < 5:
            # weekday
            midnight = "%d-%02d-%02d 00:00:00.000000-04:00" % (now.year,now.month,now.day)
            midnight_object = parse(midnight)
            four_pm = "%d-%02d-%02d 16:00:00.000000-04:00" % (now.year,now.month,now.day)
            four_pm_object = parse(four_pm)
            if now <= four_pm_object and refresh_date_object < midnight_object:
                stale = True
            elif now > four_pm_object and refresh_date_object < four_pm_object:
                stale = True
        else:
            # weekend
            last_friday = now - timedelta(days=(weekday_no-4))
            last_friday_string = "%d-%02d-%02d 16:00:00.000000-04:00" % (last_friday.year,last_friday.month,last_friday.day)
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
        if period is not None:
            if start_date is not None or end_date is not None:
                raise Exception('Cannot specify both a time period and a start/end date.')
            start_date = self._verify_period(period)
        if start_date is not None:
            dt.strptime(start_date, DATE_FORMAT)
            if start_date > str(date.today()):
                raise Exception('Requested start date in the future.')
            if end_date is not None and end_date < start_date:
                raise Exception('Requested end date is greater than requested start date.')
        if end_date is not None:
            dt.strptime(end_date, DATE_FORMAT)
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
        if period not in VALID_DAILY_WEEKLY_PERIODS:
            raise Exception('Invalid period specified; must be one of the following: ' + str(VALID_DAILY_WEEKLY_PERIODS))
        start_date = None # "All"
        # ['1M','3M','6M','1Y','2Y','5Y','10Y','All']

        print(str(start_date) + ' DAILY')
        return start_date

class Weekly(Daily):

    def __init__(self,username=USER,**kwargs):
        super(Weekly,self).__init__(username,**kwargs)

    def quote(self,symbol,period='1Y',**kwargs):
        kwargs.pop('start_date',None)
        kwargs.pop('end_date',None)
        daily_quotes = super().quote(symbol,period=period,**kwargs)
        weekly_quotes = None
        new_week = True
        self._reset_prices()
        for quote_date in daily_quotes:
            if new_week is True:
                self._reset_prices()
            day_of_week = dt.strptime(quote_date,'%Y-%m-%d').isoweekday()
        return weekly_quotes
        # ALEX

    def _reset_prices(self):
        self.adjusted_close_price = None
        self.adjusted_high_price = None
        self.adjusted_low_price = None
        self.adjusted_open_price = None
        self.adjusted_volume = None
        self.close_price = None
        self.high_price = None
        self.low_price = None
        self.open_price = None
        self.volume = None

    def _verify_period(self,period):
        start_date = super()._verify_period(period)
        print(str(start_date) + ' WEEKLY')

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

class Intraday(alphavantage.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Intraday,self).__init__(username,**kwargs)
        self.data_readwriter = data.Connection(self.username,**kwargs)

    def quote(self,symbol,interval='1',**kwargs):
        # Default interval results:
        # 
        # 1 minute intervals: 2 months
        # 60 minute intervals: 12 months
        # 
        # Note that the source also offers the following intervals: 5, 15, and 30 minutes.
        #
        # This process returns both adjusted and unadjusted quotes.
        #
        valid_intervals = ['1','60']
        if interval not in valid_intervals:
            raise Exception('Invalid interval specified for intraday quote.')
        data = {
            'interval': interval + 'min',
            'outputsize': 'full',
            'symbol': str(symbol).upper()
        }
        response = self.request('TIME_SERIES_INTRADAY',data)
        # Get adjusted data, blend into results
        return response
