import collections, datetime, json, os, re, shutil, socket, subprocess, time

from datetime import date, datetime as dt, timedelta
from dateutil import tz
from dateutil.parser import parse
from file_read_backwards import FileReadBackwards
from jsonschema import validate
from urllib.request import urlretrieve

import olympus.securities.equities.data as data
import olympus.securities.equities.data.alphavantage as alphavantage
import olympus.securities.equities.data.tdameritrade as ameritrade
import olympus.securities.equities.data.symbols as symbols

from olympus import DATE_STRING_FORMAT, Dates, FileFinder, Return, Series, USER
from olympus.securities import Quote
from olympus.securities.equities import SCHEMA_FILE_DIRECTORY
from olympus.securities.equities.data import REQUEST_TIMEOUT, TIMEZONE
from olympus.securities.equities.data.datetime import DateVerifier
from olympus.securities.equities.data.schema import ADJUSTMENTS_SCHEMA, DIVIDENDS_SCHEMA, PRICE_SCHEMA, SPLITS_SCHEMA, SchemaParser

socket.setdefaulttimeout(REQUEST_TIMEOUT) # For urlretrieve

PRICE_FORMAT = [ "Open", "High", "Low", "Close", "Volume", "Adjusted Open", "Adjusted High", "Adjusted Low", "Adjusted Close", "Adjusted Volume" ]
VALID_DAILY_WEEKLY_PERIODS = {'1M':30,'3M':91,'6M':183,'1Y':365,'2Y':730,'5Y':1825,'10Y':3652,'20Y':7305,'All':None}
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
            "Price Dividend Adjustment" : <float>,
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

# Classes for returned adjustment data

class _Adjustments(Series):

    def __init__(self,adjustment_type,data,query_date):
        super(_Adjustments,self).__init__()
        self.query_date = query_date
        if data is None:
            return
        schema_parser = SchemaParser()
        if adjustment_type == 'dividend':
            json_schema = DIVIDENDS_SCHEMA
        elif adjustment_type == 'split':
            json_schema = SPLITS_SCHEMA
        elif adjustment_type == 'merged':
            json_schema = ADJUSTMENTS_SCHEMA
        else:
            raise Exception('Unrecognized adjustment type ' + str(adjustment_type) + 'given to _Adjustments object')
        if adjustment_type == 'dividend' or adjustment_type == 'split':
            for entry in data:
                database_format = schema_parser.database_format_columns(json_schema)
                adjustment_data = {}
                format_index = 0
                for key in database_format:
                    try:
                        adjustment_data[key] = entry[format_index]
                    except IndexError:
                        break
                    except:
                        raise
                    format_index = format_index + 1
                data_object = Return(json_schema,adjustment_data)
                self.add(data_object)
        else:
            for entry in data:
                if 'Date' in entry:
                    entry['Date'] = entry['Date'].replace(tzinfo=tz.gettz(TIMEZONE))
                data_object = Return(json_schema,entry)
                self.add(data_object)
        self.sort('date',reverse=True)

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
        self.date_utils = Dates()
        self.schema_parser = SchemaParser()
        self.split_adjusted_symbol = None
        self.split_data_date = None

    def adjustments(self,symbol,**kwargs):
        # Returns all split and dividend adjustments for an equity's as-traded prices.
        # Adjustments are returned as a date-ordered array, with the most recent date first.
        symbol = str(symbol).upper()
        symbol_verify = kwargs.get('symbol_verify',True)
        if symbol_verify is True:
            self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        adjustments_collection = 'price.' + symbol
        collection = self.db[adjustments_collection]
        adjustments_data = collection.find_one({ 'Adjustment': 'Merged' },{ '_id': 0 })
        if adjustments_data is None:
            regen = True
        else:
            dividends_query_time = self.date_utils.utc_date_to_timezone_date(adjustments_data['Time Dividends'],TIMEZONE)
            splits_query_time = self.date_utils.utc_date_to_timezone_date(adjustments_data['Time Splits'],TIMEZONE)
        if regen is True or self._is_stale_data(dividends_query_time) or self._is_stale_data(splits_query_time):
            splits = self.splits(symbol,**kwargs)
            splits_date = splits.query_date
            splits.sort('date')
            dividends = self.dividends(symbol,**kwargs) 
            dividends_date = dividends.query_date
            dividends.sort('date')
            adjustments = []
            dividend = None
            split = None
            if dividends is not None:
                dividend = dividends.next()
                while dividend is not None:
                    if dividend.get('adjusted_dividend') is not None:
                        dividend_adjustment = dividend.adjusted_dividend
                    else:
                        dividend_adjustment = dividend.dividend
                    dividend_written = False
                    split = splits.next()
                    while split is not None:
                        if dividend.date > split.date:
                            adjustments.append({ 'Date': dividend.date, 'Dividend': dividend_adjustment })
                            dividend_written = True
                            break
                        elif dividend.date == split.date:
                            adjustments.append({ 'Date': dividend.date, 'Dividend': dividend_adjustment, 'Price Adjustment': split.price_dividend_adjustment, 'Volume Adjustment': split.volume_adjustment })
                            dividend_written = True
                            break
                        else: # dividend_date < split_date
                            adjustments.append({ 'Date': split.date, 'Price Adjustment': split.price_dividend_adjustment, 'Volume Adjustment': split.volume_adjustment })
                        split = splits.next()
                    if dividend_written is False:
                        adjustments.append({ 'Date': dividend.date, 'Dividend': dividend_adjustment })
                    dividend = dividends.next()
            if splits is not None:
                if split is None:
                    split = splits.next()
                while split is not None:
                    adjustments.append({ 'Date': split.date, 'Price Adjustment': split.price_dividend_adjustment, 'Volume Adjustment': split.volume_adjustment })
                    split = splits.next()
            if len(adjustments) == 0:
                adjustments = None
            else:
                adjustments = sorted(adjustments, key=lambda k: k['Date'], reverse=True)
            write_dict = {}
            write_dict['Time'] = dt.now().astimezone()
            write_dict['Adjustment'] = 'Merged'
            write_dict['Time Dividends'] = dividends_date
            write_dict['Time Splits'] = splits_date
            write_dict['Adjustments'] = adjustments
            collection.delete_many({ 'Adjustment': 'Merged' })
            collection.insert_one(write_dict)
            returndata = adjustments
            query_date = write_dict['Time']
        else:
            returndata = adjustments_data['Adjustments']
            query_date = adjustments_data['Time']
        return_object = _Adjustments('merged',returndata,query_date)
        return return_object

    def dividends(self,symbol,**kwargs):
        symbol = str(symbol).upper()
        symbol_verify = kwargs.get('symbol_verify',True)
        if symbol_verify is True:
            self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        dividend_collection = 'price.' + symbol
        target_file = self.download_directory()+symbol+'-dividends.csv'
        collection = self.db[dividend_collection]
        dividend_data = collection.find_one({ 'Adjustment': 'Dividends' },{ '_id': 0 })
        query_date = None
        stale = False
        start_dividend_date = None
        end_dividend_date = None
        if dividend_data is not None:
            query_date = self.date_utils.utc_date_to_timezone_date(dividend_data['Time'])
            if dividend_data['Start Date'] is not None:
                start_dividend_date = self.date_utils.utc_date_to_timezone_date(dividend_data['Start Date'],TIMEZONE)
            else:
                start_dividend_date = None
            if dividend_data['End Date'] is not None:
                end_dividend_date = self.date_utils.utc_date_to_timezone_date(dividend_data['End Date'],TIMEZONE)
            else:
                end_dividend_date = None
        if regen is False and dividend_data is not None:
            stale = self._is_stale_data(query_date)
        elif dividend_data is None:
            regen = True
        returndata = None
        if stale is True or regen is True:
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=0&period2=9999999999&events=div'
            response = urlretrieve(url,target_file)
            json_dividends = None
            with open(target_file,'r') as f:
                if not re.match(r'^Date,Dividends',f.readline()):
                    raise Exception('First line of symbol dividend data .csv file does not match expected format.')
                for line in f:
                    json_dividend = []
                    line = line.rstrip()
                    pieces = line.rstrip().split(',')
                    dividend_date = dt.strptime(pieces[0],DATE_STRING_FORMAT).replace(tzinfo=tz.gettz(TIMEZONE))
                    json_dividend.append(dividend_date)
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
                        json_dividend.append(round(float(adjustment_factors.price_dividend_adjustment) * adjusted_dividend,2))
                    json_dividend.append(adjusted_dividend)
                    if json_dividends is None:
                        json_dividends = []
                    json_dividends.append(json_dividend)
                write_dict = {}
                write_dict['Time'] = dt.now().astimezone()
                write_dict['Adjustment'] = 'Dividends'
                database_format = self.schema_parser.database_format_columns(DIVIDENDS_SCHEMA)
                write_dict['Format'] = database_format
                write_dict['Start Date'] = start_dividend_date
                write_dict['End Date'] = end_dividend_date
                if json_dividends is not None:
                    json_dividends = sorted(json_dividends, key=lambda k: k[0], reverse=True)
                write_dict['Dividends'] = json_dividends
                collection.delete_many({ 'Adjustment': 'Dividends' })
                collection.insert_one(write_dict)
                query_date = write_dict['Time']
                returndata = write_dict['Dividends']
            os.remove(target_file)
        if returndata is None and dividend_data is not None:
            # Database dates need to be made time zone aware
            index = 0
            for dividend in dividend_data['Dividends']:
                dividend_data['Dividends'][index][0] = dividend_data['Dividends'][index][0].replace(tzinfo=tz.gettz(TIMEZONE))
                index = index + 1
            returndata = dividend_data['Dividends']
        return_object = _Adjustments('dividend',returndata,query_date)
        return return_object

    def splits(self,symbol,**kwargs):
        symbol = str(symbol).upper()
        symbol_verify = kwargs.get('symbol_verify',True)
        if symbol_verify is True:
            self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        split_collection = 'price.' + symbol
        target_file = self.download_directory()+symbol+'-splits.csv'
        collection = self.db[split_collection]
        split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0 })
        query_date = None
        stale = False
        start_split_date = None
        end_split_date = None
        if split_data is not None:
            query_date = self.date_utils.utc_date_to_timezone_date(split_data['Time'])
            if split_data['Start Date'] is not None:
                start_split_date = self.date_utils.utc_date_to_timezone_date(split_data['Start Date'],TIMEZONE)
            else:
                start_split_date = None
            if split_data['End Date'] is not None:
                end_split_date = self.date_utils.utc_date_to_timezone_date(split_data['End Date'],TIMEZONE)
            else:
                end_split_date = None
        if regen is False and split_data is not None:
            stale = self._is_stale_data(query_date)
        elif split_data is None:
            regen = True
        returndata = None
        if stale is True or regen is True:
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=0&period2=9999999999&events=split'
            response = urlretrieve(url,target_file)
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
                split_date_string = split_date
                json_split = []
                split_date = dt.strptime(split_date,DATE_STRING_FORMAT).replace(tzinfo=tz.gettz(TIMEZONE))
                json_split.append(split_date)
                if (start_split_date is None or start_split_date >= split_date):
                    start_split_date = split_date
                if (end_split_date is None or end_split_date <= split_date):
                    end_split_date = split_date
                (numerator,denominator) = splits[split_date_string].rstrip().split(':')
                json_split.append(int(numerator))
                json_split.append(int(denominator))
                numerator = float(numerator)
                denominator = float(denominator)
                price_dividend_adjustment = (numerator/denominator)
                volume_adjustment = (denominator/numerator)
                if last_split is not None:
                    price_dividend_adjustment = price_dividend_adjustment * float(last_split[3])
                    volume_adjustment = volume_adjustment * float(last_split[4])
                json_split.append(float(price_dividend_adjustment))
                json_split.append(float(volume_adjustment))
                last_split = json_split
                if json_splits is None:
                    json_splits = []
                json_splits.append(json_split)
            write_dict = {}
            write_dict['Time'] = dt.now().astimezone()
            write_dict['Adjustment'] = 'Splits'
            database_format = self.schema_parser.database_format_columns(SPLITS_SCHEMA)
            write_dict['Format'] = database_format
            write_dict['Start Date'] = start_split_date
            write_dict['End Date'] = end_split_date
            if json_splits is not None:
                json_splits = sorted(json_splits, key=lambda k: k[0], reverse=True)
            write_dict['Splits'] = json_splits
            collection.delete_many({ 'Adjustment': 'Splits' })
            collection.insert_one(write_dict)
            query_date = write_dict['Time']
            returndata = write_dict['Splits']
            os.remove(target_file)
        if returndata is None and split_data is not None:
            # Database dates need to be made time zone aware
            index = 0
            for split in split_data['Splits']:
                split_data['Splits'][index][0] = split_data['Splits'][index][0].replace(tzinfo=tz.gettz(TIMEZONE))
                index = index + 1
            returndata = split_data['Splits']
        return_object = _Adjustments('split',returndata,query_date)
        return return_object

    def split_adjustment(self,symbol,value_date,**kwargs):
        # Returns split adjustment values for unadjusted prices on a given date
        symbol = str(symbol).upper()
        if self.split_adjusted_symbol is None or self.split_adjusted_symbol != symbol or self.split_data_date is None or self._is_stale_data(self.split_data_date):
            self.splits_series = self.splits(symbol,**kwargs) 
            self.split_data_date = self.splits_series.query_date
            self.split_adjusted_symbol = symbol
        if self.splits_series.have_objects() is True:
            self.splits_series.sort('date')
            entry = self.splits_series.next(reset=True)
            while entry is not None:
                if value_date < entry.date:
                    return(entry)
                entry = self.splits_series.next()
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
            if now <= nine_pm_object and refresh_date < nine_pm_yesterday_object:
                stale = True
            elif now > nine_pm_object and refresh_date < nine_pm_object:
                stale = True
        else:
            # Weekend
            last_friday = now - timedelta(days=(weekday_no-4))
            last_friday_string = "%d-%02d-%02d 21:00:00.000000-04:00" % (last_friday.year,last_friday.month,last_friday.day)
            last_friday_object = parse(last_friday_string)
            if refresh_date < last_friday_object:
                stale = True
        return stale

class _PriceAdjuster(Adjustments):
    '''
An internal class used by both daily and intraday price quotes to apply price and volume adjustments.
Built with the understanding that daily close prices are split adjusted
    '''

    DEFAULT_DIVIDEND_ADJUSTMENT = 1.0
    DEFAULT_PRICE_ADJUSTMENT = 1
    DEFAULT_VOLUME_ADJUSTMENT = 1.0

    def __init__(self,symbol,username=USER,**kwargs):
        super(_PriceAdjuster,self).__init__(username)
        regen = kwargs.get('regen',False)
        symbol_verify = kwargs.get('symbol_verify',True)
        self.symbol_adjustments = self.adjustments(symbol,regen=regen,symbol_verify=symbol_verify)
        if self.symbol_adjustments is not None:
            self.symbol_adjustments.sort('date',reverse=True)
            self.next_adjustment = self.symbol_adjustments.next()
            self.dividend_adjustment = self.DEFAULT_DIVIDEND_ADJUSTMENT
            self.price_adjustment = self.DEFAULT_PRICE_ADJUSTMENT
            self.volume_adjustment = self.DEFAULT_VOLUME_ADJUSTMENT

    def date_iterator(self,quote_date,daily_close):
        '''
        Called repeatedly over a sequence of dates to calculate proper price/volume adjustments.

        Dividend adjustments for dates prior to the ex-dividend date are done according to the following calculation:

        Closing price on day prior to dividend - dividend amount
        -------------------------------------------------------- = Adjustment factor
               Closing price on day prior to dividend

        Multiply the adjustment factor by all prices before the ex-dividend date to calculate adjusted prices.

        In the common case of multiple historical dividends, the adjustment factors are CUMULATIVE, which means that
        the calculated adjustment factor for a specific date must be multiplied by all later adjustment factors
        to get the actual adjustment factor for that date. Therefore, calculating adjustments requires that we know
        closing prices for the security.

        The data sources give us split-adjusted prices, which we rely on to calculate all other prices. Therefore,
        the above calculation uses the split-adjusted closing price and the split-adjusted dividend.
        '''
        if self.next_adjustment is not None and quote_date < self.next_adjustment.date and daily_close is not None:
            if hasattr(self.next_adjustment,'dividend'):
                self.dividend_adjustment = self.dividend_adjustment * ((float(daily_close) - float(self.next_adjustment.dividend)) / float(daily_close))
            if hasattr(self.next_adjustment,'price_adjustment'):
                # These two always show up together (reciprocals)
                self.price_adjustment = self.next_adjustment.price_adjustment
                self.volume_adjustment = self.next_adjustment.volume_adjustment
            self.next_adjustment = self.symbol_adjustments.next()

    def have_adjustments(self):
        if self.symbol_adjustments is not None:
            return True
        return False

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
      from Yahoo! Finance historical quotes. These records include "Price Dividend Adjustment" and
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
        date_verifier = DateVerifier()
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
            date_verifier.verify_date(start_date)
            if start_date >= self.today:
                raise Exception('Requested start date in not in the past.')
            if end_date is not None and end_date <= start_date:
                raise Exception('Requested start date is not older than requested end date.')
        if end_date is not None:
            date_verifier.verify_date(end_date)
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
            response = urlretrieve(url,target_file)
            with open(target_file,'r') as f:
                self._verify_csv_daily_format(f.readline())
                if self.end_date_daily is not None:
                    compare_line = f.readline().rstrip()
                    pieces = compare_line.rstrip().split(',')
                    if round(interval_data['Quotes'][self.end_date_daily][3],2) != round(float(pieces[5]),2):
                        # There's been a price adjustment, regenerate everything
                        regen = True
            if regen is False:
                adjuster = _PriceAdjuster(symbol,self.username,regen=regen_adjustments,symbol_verify=False)
                subprocess.check_output("/usr/bin/sed -i '1d' " + target_file, shell=True)
                with FileReadBackwards(target_file, encoding="utf-8") as f:
                    for line in f:
                        (json_quote,interval_date) = self._parse_daily(line,adjuster)
                        if json_quote is not None:
                            collection.update_one({'Interval': '1d'},{ "$set": {'Quotes.'+interval_date: json_quote}}, upsert=True)
                            interval_data['Quotes'][interval_date] = json_quote
                    collection.update_one({'Interval': '1d'},{ "$set":  {'End Date': self.end_date_daily, 'Start Date': self.start_date_daily, 'Time': str(now)}})
            os.remove(target_file)
        if regen is True:
            adjuster = _PriceAdjuster(symbol,self.username,regen=regen_adjustments,symbol_verify=False)
            url = self._daily_quote_url(symbol)
            response = urlretrieve(url,target_file)
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
                    (json_quote,interval_date) = self._parse_daily(line,adjuster)
                    if json_quote is not None:
                        json_quotes[interval_date] = json_quote
            write_dict = {}
            write_dict['Time'] = str(now)
            write_dict['Interval'] = '1d'
            write_dict['Format'] = PRICE_FORMAT
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
            start_date = dt.strptime(start_date,DATE_STRING_FORMAT)
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,DATE_STRING_FORMAT) >= start_date}
        if end_date is not None:
            end_date = dt.strptime(end_date,DATE_STRING_FORMAT)
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,DATE_STRING_FORMAT) <= end_date}
        # Format returned data using data headers
        formatted_returndata = {}
        details_length = len(PRICE_FORMAT)
        for quote_date in returndata:
            formatted_returndata[quote_date] = {}
            quote_length = len(returndata[quote_date])
            for index in range(0, details_length):
                if index >= quote_length:
                    formatted_returndata[quote_date][PRICE_FORMAT[index]] = returndata[quote_date][index-5]
                else:
                    formatted_returndata[quote_date][PRICE_FORMAT[index]] = returndata[quote_date][index]
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

    def _parse_daily(self,line,adjuster):
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
        if adjuster.have_adjustments() is False:
            quote.append(round(float(pieces[1]),2)) # Open
            quote.append(round(float(pieces[2]),2)) # High
            quote.append(round(float(pieces[3]),2)) # Low
            quote.append(round(float(pieces[4]),2)) # Close
            quote.append(int(pieces[6])) # Volume
        else:
            adjuster.date_iterator(interval_date,float(pieces[4]))
            if adjuster.get_dividend_adjustment() == 1.0 and adjuster.get_price_adjustment() == 1:
                quote.append(round(float(pieces[1]),2)) # Open
                quote.append(round(float(pieces[2]),2)) # High
                quote.append(round(float(pieces[3]),2)) # Low
                quote.append(round(float(pieces[4]),2)) # Close
                quote.append(int(pieces[6])) # Volume
            else:
                quote.append(round(float(pieces[1]) * float(adjuster.get_price_adjustment()),2)) # Open
                quote.append(round(float(pieces[2]) * float(adjuster.get_price_adjustment()),2)) # High
                quote.append(round(float(pieces[3]) * float(adjuster.get_price_adjustment()),2)) # Low
                quote.append(round(float(pieces[4]) * float(adjuster.get_price_adjustment()),2)) # Close
                quote.append(int(int(pieces[6]) * float(adjuster.get_volume_adjustment()))) # Volume
                # Adjusted prices rounded to 6 places for better accuracy when plotting small adjusted numbers
                quote.append(round(float(pieces[1]) * adjuster.get_dividend_adjustment(),6)) # Adjusted open
                quote.append(round(float(pieces[2]) * adjuster.get_dividend_adjustment(),6)) # Adjusted high
                quote.append(round(float(pieces[3]) * adjuster.get_dividend_adjustment(),6)) # Adjusted low
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
            day_of_week = dt.strptime(quote_date,DATE_STRING_FORMAT).isoweekday()
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
            day_of_week = dt.strptime(start_date,DATE_STRING_FORMAT).isoweekday()
            if day_of_week > 1 and day_of_week < 6:
                start_date = str(dt.strptime(start_date,DATE_STRING_FORMAT) - timedelta(days=(day_of_week-1)))[0:10]
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

    def compare_quotes(self,quote):
        for item in ['Open','Adjusted Open']:
            if getattr(self,item) is None:
                setattr(self,item, quote[item])
        for item in ['High','Adjusted High']:
            if getattr(self,item) is None or quote[item] > getattr(self,item):
                setattr(self,item,quote[item])
        for item in ['Low','Adjusted Low']:
            if getattr(self,item) is None or quote[item] < getattr(self,item):
                setattr(self,item,quote[item])
        for item in ['Close','Adjusted Close']:
            setattr(self,item,quote[item])
        for item in ['Volume','Adjusted Volume']:
            setattr(self,item,getattr(self,item) + quote[item])

    def init_quote(self,quote):
        for label in PRICE_FORMAT:
            setattr(self,label,quote[label])

    def reset_quote(self):
        for label in PRICE_FORMAT:
            setattr(self,label,None)
        setattr(self,'Adjusted Volume',0)
        setattr(self,'Volume',0)

    def set_quote(self):
        quote = {}
        for label in PRICE_FORMAT:
            quote[label] = getattr(self,label)
        return quote

class Intraday(ameritrade.Connection):
    '''
This class focuses on the minute-by-minute price quotes available via the TD Ameritrade API.
    '''

    DEFAULT_INTRADAY_FREQUENCY = 30
    DEFAULT_INTRADAY_PERIOD = 10
    # Keys: Frequency of quote (in minutes)
    # Values: Number of days into the past from today for which data is available for given frequency, inclusive of today's date
    VALID_INTRADAY_FREQUENCIES = {1:50, 5:260, 10:260, 15:260, 30:260}
    VALID_INTRADAY_PERIODS = [1, 2, 3, 4, 5, 10]

    def __init__(self,username=USER,**kwargs):
        super(Intraday,self).__init__(username,**kwargs)
        self.symbol_reader = symbols.Read(username,**kwargs)

    def quote(self,symbol,frequency=DEFAULT_INTRADAY_FREQUENCY,**kwargs):
        symbol = str(symbol).upper()
        self.symbol_reader.get_symbol(symbol)
        self.valid_frequency(frequency)
        need_extended_hours_data = kwargs.get('need_extended_hours_data',True)
        period = kwargs.get('period',None)
        end_date = kwargs.get('end_date',None)
        start_date = kwargs.get('start_date',None)
        params = { 'frequency': frequency, 'frequencyType': 'minute', 'needExtendedHoursData': need_extended_hours_data, 'periodType': 'day' }
        period = self.valid_period(period,start_date,end_date)
        if period is not None:
            params['period'] = period
        (start_date, end_date) = self._verify_dates(start_date,end_date,frequency,period)
        if start_date is not None:
            params['startDate'] = start_date
        if end_date is not None:
            params['endDate'] = end_date
        response = self.request('marketdata/' + symbol + '/pricehistory',params)
        if response['symbol'] != symbol:
            raise Exception('Incorrect symbol ' + str(response['symbol']) + ' returned by API call.')
        return_object = Series()
        adjuster = _PriceAdjuster(symbol,self.username,regen=False,symbol_verify=False)
        last_quote_date = None
        daily_close = None
        candle_count = len(response['candles'])
        candle_index = candle_count - 1
        # "response['candles']" is a list in ascending date order, so read the list backwards to correctly apply adjustments
        for quote in reversed(response['candles']): # Most recent date/time first
            quote_date = dt.fromtimestamp(quote['datetime']/1000)
            quote['datetime'] = quote_date.replace(tzinfo=tz.gettz(TIMEZONE))
            quote_date_midnight = dt(quote_date.year,quote_date.month,quote_date.day)
            quote_date_midnight = quote_date_midnight.replace(tzinfo=tz.gettz(TIMEZONE))
            data = {}
            if adjuster.have_adjustments() is True:
                data['datetime'] = quote['datetime']
                adjuster.date_iterator(quote_date_midnight,daily_close)
                for key in quote:
                    if key == 'datetime':
                        continue
                    adjusted_key = 'adjusted ' + key
                    if key == 'volume':
                        # Volume is split-adjusted already.
                        # For true volume, apply the adjuster (un)adjustment
                        data[key] = int(quote[key] * adjuster.volume_adjustment)
                        data[adjusted_key] = quote[key]
                    else:
                        # Price is split-adjusted already.
                        # For true price, apply the price (un)adjustment
                        # For adjusted price, apply the dividend adjustment
                        data[key] = round(quote[key] * adjuster.price_adjustment,2)
                        data[adjusted_key] = round(quote[key] * adjuster.dividend_adjustment,6)
            else:
                data = quote
            data_object = Return(PRICE_SCHEMA,data)
            return_object.add(data_object)
        return_object.sort('date')
        return return_object

    def oldest_available_date(self,frequency):
        now = dt.now().astimezone()
        return (dt(now.year, now.month, now.day, 0, 0, 0) - timedelta(self.VALID_INTRADAY_FREQUENCIES[frequency] - 1)).replace(tzinfo=tz.gettz()) # Inclusive of today, so minus 1

    def valid_frequency(self,frequency):
        if frequency not in self.VALID_INTRADAY_FREQUENCIES.keys():
            raise Exception('Invalid frequency specified; must be one of the following: ' + ', ' . join(self.VALID_INTRADAY_FREQUENCIES))

    def valid_period(self,period=None,start_date=None,end_date=None):
        if period is not None and period not in self.VALID_INTRADAY_PERIODS:
            raise Exception('Invalid period specified; must be one of the following: ' + ', ' . join(self.VALID_INTRADAY_PERIODS))
        if period is not None and start_date is not None:
            raise Exception('The keyword argument "period" cannot be declared with the "start_date" keyword argument')
        if period is None and start_date is None and end_date is None:
            period = self.DEFAULT_INTRADAY_PERIOD
        return period

    def _verify_dates(self,start_date,end_date,frequency,period):
        date_verifier = DateVerifier()
        (start_date,end_date) = date_verifier.verify_date_range(start_date,end_date,null_start_date=True,keep_null_end_date=True,allow_future_end_date=False)
        oldest_available_date = self.oldest_available_date(frequency)
        if start_date is not None:
            if start_date < oldest_available_date:
                raise Exception('For a minute frequency of ' + str(frequency) + ', the oldest available date is ' + str(oldest_available_date) + '.')
            start_date = start_date.strftime('%s')
            start_date = int(start_date) * 1000 # Milliseconds per API
        if end_date is not None:
            if end_date < oldest_available_date:
                raise Exception('For a minute frequency of ' + str(frequency) + ', the oldest available date is ' + str(oldest_available_date) + '.')
            if period is not None and start_date is None:
                if end_date - timedelta(days=period-1) < oldest_available_date:
                    raise Exception('Cannot retrieve data for requested end date ' + end_date + ' and period ' + str(period) + ' with frequency ' + str(frequency) + ' since oldest available date is ' + str(oldest_available_date) + '.')
            end_date = end_date.strftime('%s')
            end_date = int(end_date) * 1000 # Milliseconds per API
        return start_date, end_date

class _LatestQuotes(Series):

    def __init__(self,schema):
        super(_LatestQuotes,self).__init__()
        self.json_schema = schema
        self.unknown_symbols = None
        self.unquoted_symbols = None

    def add_symbol(self,symbol,data):
        latest_price_object = Return(self.json_schema,data)
        self.add(latest_price_object)

    def add_unknown_symbol(self,symbol):
        symbol = symbol.upper()
        if self.unknown_symbols is None:
            self.unknown_symbols = []
        if symbol not in self.unknown_symbols:
            self.unknown_symbols.append(symbol)

    def add_unquoted_symbol(self,symbol):
        symbol = symbol.upper()
        if self.unquoted_symbols is None:
            self.unquoted_symbols = []
        if symbol not in self.unquoted_symbols:
            self.unquoted_symbols.append(symbol)

    def get_symbol(self,symbol):
        return self.get_by_attribute('symbol',symbol)

    def get_quotes(self):
        return self.objects()

class Latest(ameritrade.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Latest,self).__init__(username,**kwargs)
        self.symbol_reader = symbols.Read(username,**kwargs)
        file_finder = FileFinder()
        schema_file_name = file_finder.schema_file(SCHEMA_FILE_DIRECTORY,'LatestPriceQuote')
        with open(schema_file_name) as schema_file:
            self.json_schema = json.load(schema_file)

    def quote(self,symbol,**kwargs):
        return_object = _LatestQuotes(self.json_schema)
        params = {}
        # Symbol can be a string or array (list of symbols)
        if isinstance(symbol, str):
            symbol = str(symbol).upper()
            try:
                result = self.symbol_reader.get_symbol(symbol)
            except symbols.SymbolNotFoundError:
                return_object.add_unknown_symbol(symbol)
                return return_object
            except:
                raise
            params['symbol'] = symbol
        elif isinstance(symbol, list):
            symbols = [str(x).upper() for x in symbol]
            result = self.symbol_reader.get_symbols(symbols)
            if result.unknown_symbols is not None:
                for unknown_symbol in result.unknown_symbols:
                    return_object.add_unknown_symbol(unknown_symbol)
                if result.have_objects() is False:
                    return return_object
            params['symbol'] = ','.join(result.get_symbols())
        else:
            raise Exception('Parameter "symbol" must be a string or a list of strings.')
        response = self.request('marketdata/quotes',params,'GET',with_apikey=True)
        have_quoted_symbols = False
        if isinstance(symbol, str):
            if symbol not in response:
                return_object.add_unquoted_symbol(symbol)
                return return_object
            have_quoted_symbols = True
        elif isinstance(symbol, list):
            for uc_symbol in symbols:
                if uc_symbol not in response and return_object.unknown_symbols is not None and uc_symbol not in return_object.unknown_symbols:
                    return_object.add_unquoted_symbol(uc_symbol)
                else:
                    have_quoted_symbols = True
        if have_quoted_symbols is True:
            for quote_symbol in response:
                quote = response[quote_symbol]
                return_object.add_symbol(quote_symbol,quote)
        return return_object
