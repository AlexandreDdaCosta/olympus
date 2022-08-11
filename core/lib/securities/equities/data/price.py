import collections, datetime, json, os, re, urllib.request, wget

from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse

from olympus import USER, User

import olympus.securities.equities.data as data
import olympus.securities.equities.data.alphavantage as alphavantage
import olympus.securities.equities.data.tdameritrade as ameritrade
import olympus.securities.equities.data.symbols as symbols

STORED_DIVIDEND_FORMAT = [ "Dividend", "Adjusted Dividend" ]
STORED_PRICE_FORMAT = [ "Open", "High", "Low", "Close", "Volume", "Adjusted Close", "Adjusted Open", "Adjusted High", "Adjusted Low" ]
STORED_SPLIT_FORMAT = [ "Numerator", "Denominator", "Price/Dividend Adjustment", "Volume Adjustment" ]

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
            "Numerator" : "<integer>",
            "Denominator" : "<integer>",
            "Price/Dividend Adjustment" : "<float>",
            "Volume Adjustment" : "<float>"
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
            "Dividend" : "<float>"[,
            "Adjusted Dividend" : "<float>"]
        },
        <more dividends>
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
2. Split adjustments are cumulative, starting from the most recent date and extended into the past
   to the first recorded split. This allows for simple calculations when doing related price, volume,
   and dividend adjustments. Note that price and dividend adjustments are identical. Also note
   that adjustments begin on the date they are recorded.
3. Adjusted dividend numbers are included only when adjusted for splits.
4. Adjusted price figures within brackets are included only when they differ from as-traded numbers.

'''

class Adjustments(data.Connection):
    '''
Yahoo! Finance historical quotes are the data source for split history due to the data
being free and having a deep history.

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

    def splits(self,symbol,**kwargs):
        symbol = str(symbol).upper()
        symbol_data = self.symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        split_collection = 'price.' + symbol
        target_file = self.download_directory()+symbol+'-splits.csv'
        collection = self.db[split_collection]
        split_data = collection.find_one({ 'Adjustment': 'Splits' },{ '_id': 0 })
        stale = False
        start_split_date = None
        end_split_date = None
        now = dt.now().astimezone()
        if split_data is not None:
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
                json_split.append(numerator)
                json_split.append(denominator)
                numerator = float(numerator)
                denominator = float(denominator)
                price_dividend_adjustment = (denominator/numerator)
                volume_adjustment = (numerator/denominator)
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
            write_dict['Time'] = str(now)
            write_dict['Adjustment'] = 'Splits'
            write_dict['Format'] = STORED_SPLIT_FORMAT
            write_dict['Start Date'] = start_split_date
            write_dict['End Date'] = end_split_date
            write_dict['Splits'] = json_splits
            collection.delete_many({ 'Adjustment': 'Splits' })
            collection.insert_one(write_dict)
            returndata = write_dict['Splits']
            os.remove(target_file)

        if returndata is None:
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
            return collections.OrderedDict(sorted(formatted_returndata.items()))
        return None

    def _is_stale_data(self,refresh_date):
        # Query source:
        # If now is a weekday and before 4:00 PM, generated before today
        # If now is a weekday and after 4:00 PM, generated before 4:00 PM today
        # If now is a weekend day, generated before 4:00 last Friday
        stale = False
        refresh_date_object = parse(refresh_date)
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

1. Prices are all adjusted. Yahoo!'s plain "open/high/low/close/volume" figures are adjusted for stock splits only.
   Available data also includes an "adjusted close", but not any other adjusted data. By calculating an
   "adjustment coefficient" using "close" and "adjusted close", it's possible to determine the remaining
   adjusted data EXCEPT for volume, which is only adjusted for stock splits.  The "adjusted close" is adjusted for
   both stock splits and dividends.
2. Based on the formatting of the price data, daily data is therefore saved as follows:
   a. Maintain up-to-date records of a symbol's historical price splits, also available for download from Yahoo!
      Finance historical quotes.
   b. "Adjusted Close/Open/High/Low" are stored as the true adjusted data, without alterations. "Volume" is 
      stored as the true adjusted volume.
   c. To derive as-traded prices, take "Open/High/Low/Close" and compensate for stock splits by dividing the 
      numerator by the denominator used in the split specification. For example, if a split is 2 for 1 (2:1),
      2/1 = 2, so multiply all quotes by 2 to get the correct price. Continuing this example:
      1) After the Yahoo! adjustment, a company shares are quoted as trading 50 pre-split.
      2) 50 * 2 = 100, which was the as-traded price of the shares pre-split.
   d. To derive as-traded volume, take "Volume" and compensate for stock splits by dividing the denominator by
      the numerator. Continuing the previous example:
      1) After the Yahoo! adjustment, a company is recorded as trading 1000 shares pre-split.
      2) 1000 * (1/2) = 500, which was the as-traded volume of the shares pre-split.
3. When adjusted for a series of splits, the compensation factor is cumulative. For example, when adjusted for
   two 2:1 splits, the price adjustment would be:
   (2/1) * (2/1) = 4
   So if a company's shares are quoted as trading 50 before both splits, the as-traded price would be 50 * 4 = 200
   The volume adjustment for two 2:1 splits would be:
   (1/2) * (1/2)  = 1/4
   So if a company is recorded as trading 1000 shares before both splits, the as-traded volume would be
   1000 * (1/4) = 250 shares.

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
        start_date = kwargs.get('start_date',None)
        end_date = kwargs.get('end_date',None)
        now = dt.now().astimezone()
        price_collection = 'price.' + symbol
        period1 = '0'
        period2 = '9999999999' # To the present day, and beyooond
        returndata = None

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
            stale = self._is_stale_data(split_data['Time'])
        elif interval_data is None:
            regen = True
        if regen is False and stale is True:
            if self.end_date_daily is not None:
                year,month,day = map(int,self.end_date_daily.rstrip().split('-'))
                period1 = str(int(dt(year, month, day, 0, 0, 0).timestamp()))
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=' + period1 + '&period2=' + period2 + '&interval=1d&events=history&includeAdjustedClose=true'
            target_file = self.download_directory()+symbol+'-daily.csv'
            response = urllib.request.urlretrieve(url,target_file)
            with open(target_file,'r') as f:
                self._verify_csv_daily_format(f.readline())
                if self.end_date_daily is not None:
                    compare_line = f.readline().rstrip()
                    pieces = compare_line.rstrip().split(',')
                    if interval_data['Quotes'][self.end_date_daily][5] != str("%.2f" % float(pieces[5])):
                        # There's been a price adjustment, regenerate everything
                        regen = True
                if regen is False:
                    for line in f:
                        (json_quote,interval_date) = self._parse_daily(line)
                        collection.update_one({'Interval': '1d'},{ "$set": {'Quotes.'+interval_date: json_quote}}, upsert=True)
                        interval_data['Quotes'][interval_date] = json_quote
                    collection.update_one({'Interval': '1d'},{ "$set":  {'End Date': self.end_date_daily, 'Start Date': self.start_date_daily, 'Time': str(now)}})
            os.remove(target_file)
        if regen is True:
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=0&period2=' + period2 + '&interval=1d&events=history&includeAdjustedClose=true'
            target_file = self.download_directory()+symbol+'-daily.csv'
            response = urllib.request.urlretrieve(url,target_file)
            with open(target_file,'r') as f:
                self._verify_csv_daily_format(f.readline())
                json_quotes = {}
                for line in f:
                    (json_quote,interval_date) = self._parse_daily(line)
                    json_quotes[interval_date] = json_quote
                write_dict = {}
                write_dict['Time'] = str(now)
                write_dict['Interval'] = '1d'
                write_dict['Format'] = STORED_PRICE_FORMAT
                write_dict['Start Date'] = self.start_date_daily
                write_dict['End Date'] = self.end_date_daily
                write_dict['Quotes'] = json_quotes
                collection.delete_many({ 'Interval': '1d' })
                collection.insert_one(write_dict)
                interval_data = collection.find_one({ 'Interval': '1d'})
                returndata = write_dict['Quotes']
            os.remove(target_file)

        if returndata is None:
            returndata = interval_data['Quotes']
        # Trim data outside of requested date range
        if start_date is not None:
            start_date = dt.strptime(start_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") > start_date}
        if end_date is not None:
            end_date = dt.strptime(end_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") < end_date}
        # Format returned data using data headers
        formatted_returndata = {}
        details_length = len(STORED_PRICE_FORMAT)
        for quote_date in returndata:
            formatted_returndata[quote_date] = {}
            quote_length = len(returndata[quote_date])
            for index in range(0, details_length):
                if index >= quote_length:
                    formatted_returndata[quote_date][STORED_PRICE_FORMAT[index]] = returndata[quote_date][index-6]
                else:
                    formatted_returndata[quote_date][STORED_PRICE_FORMAT[index]] = returndata[quote_date][index]
        return collections.OrderedDict(sorted(formatted_returndata.items()))

    def _parse_daily(self,line):
        line = line.rstrip()
        pieces = line.rstrip().split(',')
        interval_date = str(pieces[0])
        if (self.start_date_daily is None or self.start_date_daily >= interval_date):
            self.start_date_daily = interval_date
        if (self.end_date_daily is None or self.end_date_daily <= interval_date):
            self.end_date_daily = interval_date
        json_quote = []
        json_quote.append(str("%.2f" % float(pieces[1])))
        json_quote.append(str("%.2f" % float(pieces[2])))
        json_quote.append(str("%.2f" % float(pieces[3])))
        json_quote.append(str("%.2f" % float(pieces[4])))
        json_quote.append(pieces[6])
        json_quote.append(str("%.2f" % float(pieces[5])))
        if (float(pieces[4]) != float(pieces[5])):
            adjustment = float(pieces[5]) / float(pieces[4])
            json_quote.append(str("%.2f" % (float(pieces[1]) * adjustment)))
            json_quote.append(str("%.2f" % (float(pieces[2]) * adjustment)))
            json_quote.append(str("%.2f" % (float(pieces[3]) * adjustment)))
        return json_quote, interval_date

    def _verify_csv_daily_format(self,first_line):
        if not re.match(r'^Date,Open,High,Low,Close,Adj Close,Volume',first_line):
            raise Exception('First line of symbol daily data .csv file does not match expected format.')

class Latest(ameritrade.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Latest,self).__init__(username,**kwargs)
        self.symbol_reader = symbols.Read(username,**kwargs)

    def quote(self,symbol,**kwargs):
        params = {}
        unknown_symbols = []
        unquoted_symbols = []
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
