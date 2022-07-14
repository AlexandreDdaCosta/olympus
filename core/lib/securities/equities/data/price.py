import collections, datetime, json, os, re, urllib.request, wget

from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse

from olympus import USER, User

import olympus.securities.equities.data as data
import olympus.securities.equities.data.alphavantage as alphavantage
import olympus.securities.equities.data.tdameritrade as ameritrade
import olympus.securities.equities.data.symbols as symbols

'''
When stored in the database, price data is split into separate collection by symbol
with the naming convention "price.<symbol>". The documents stored within each
collection are arranged as follows:

{
    "_id" : ObjectId("################"),
    "Time" : "<Last update time>"
    "Interval": "<Interval of series. Available: 1m/60m (minutes), 1d (day)>"
    "Start Time": "<Time stamp for first interval stored. One minute resolution.>"
    "End Time": "<Time stamp for last interval stored. One minute resolution.>"
    "Quotes" : {
        "<Time stamp, one minute resolution" : {
            "Open" : <quote>,
            "High" : <quote>,
            "Low" : <quote>,
            "Close" : <quote>,
            "Adjusted Close" : <quote>,
            [
            "Adjusted Open" : <quote>,
            "Adjusted High" : <quote>,
            "Adjusted Low" : <quote>,
            ]
            "Volume" : "<integer>"
},
<more intervals>
...,
{
}

Notes:

1. Adjusted prices within brackets are included only when they differ from as-traded prices.

'''

class Daily(data.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Daily,self).__init__(username,**kwargs)
        self.symbol_reader = symbols.Read(username,**kwargs)

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
        self.start_date_stored = None
        self.end_date_stored = None
        if interval_data is not None:
            self.start_date_stored = interval_data['Start Date']
            self.end_date_stored = interval_data['End Date']
        if regen is False and interval_data is not None:
            refresh_date = interval_data['Time']
            refresh_date_object = parse(refresh_date)
            # Query source:
            # If now is a weekday and before 4:00 PM, generated before today
            # If now is a weekday and after 4:00 PM, generated before 4:00 PM today
            # If now is a weekend day, generated before 4:00 last Friday
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
        elif interval_data is None:
            regen = True
        if regen is False and stale is True:
            if self.end_date_stored is not None:
                year,month,day = map(int,self.end_date_stored.rstrip().split('-'))
                period1 = str(int(dt(year, month, day, 0, 0, 0).timestamp()))
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=' + period1 + '&period2=' + period2 + '&interval=1d&events=history&includeAdjustedClose=true'
            target_file = self.download_directory()+symbol+'-daily.csv'
            response = urllib.request.urlretrieve(url,target_file)
            with open(target_file,'r') as f:
                first_line = f.readline()
                if not re.match(r'^Date,Open,High,Low,Close,Adj Close,Volume',first_line):
                    raise Exception('First line of symbol daily data .csv file does not match expected format.')
                if self.end_date_stored is not None:
                    compare_line = f.readline().rstrip()
                    pieces = compare_line.rstrip().split(',')
                    if interval_data['Quotes'][self.end_date_stored]['Adjusted Close'] != str("%.2f" % float(pieces[5])):
                        # There's been a price adjustment, regenerate everything
                        regen = True
                if regen is False:
                    for line in f:
                        (json_quote,interval_date) = self._parse(line)
                        collection.update_one({'Interval': '1d'},{ "$set": {'Quotes.'+interval_date: json_quote}}, upsert=True)
                        interval_data['Quotes'][interval_date] = json_quote
                    collection.update_one({'Interval': '1d'},{ "$set":  {'End Date': self.end_date_stored, 'Start Date': self.start_date_stored, 'Time': str(now)}})
            os.remove(target_file)
        if regen is True:
            url = 'https://query1.finance.yahoo.com/v7/finance/download/' + symbol + '?period1=0&period2=' + period2 + '&interval=1d&events=history&includeAdjustedClose=true'
            target_file = self.download_directory()+symbol+'-daily.csv'
            response = urllib.request.urlretrieve(url,target_file)
            with open(target_file,'r') as f:
                first_line = f.readline()
                # Verify retrieved csv
                if not re.match(r'^Date,Open,High,Low,Close,Adj Close,Volume',first_line):
                    raise Exception('First line of symbol daily data .csv file does not match expected format.')
                json_quotes = {}
                for line in f:
                    (json_quote,interval_date) = self._parse(line)
                    json_quotes[interval_date] = json_quote
                write_dict = {}
                write_dict['Time'] = str(now)
                write_dict['Interval'] = '1d'
                write_dict['Start Date'] = self.start_date_stored
                write_dict['End Date'] = self.end_date_stored
                write_dict['Quotes'] = json_quotes
                collection.delete_many({ 'Interval': '1d' })
                collection.insert_one(write_dict)
                interval_data = collection.find_one({ 'Interval': '1d'})
                returndata = write_dict['Quotes']
            os.remove(target_file)

        if returndata is None:
            returndata = interval_data['Quotes']
        if start_date is not None:
            start_date = dt.strptime(start_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") > start_date}
        if end_date is not None:
            end_date = dt.strptime(end_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") < end_date}
        return collections.OrderedDict(sorted(returndata.items()))

    def _parse(self,line):
        line = line.rstrip()
        pieces = line.rstrip().split(',')
        json_quote = {}
        interval_date = str(pieces[0])
        if (self.start_date_stored is None or self.start_date_stored >= interval_date):
            self.start_date_stored = interval_date
        if (self.end_date_stored is None or self.end_date_stored <= interval_date):
            self.end_date_stored = interval_date
        json_quote['Open'] = str("%.2f" % float(pieces[1]))
        json_quote['High'] = str("%.2f" % float(pieces[2]))
        json_quote['Low'] = str("%.2f" % float(pieces[3]))
        json_quote['Close'] = str("%.2f" % float(pieces[4]))
        json_quote['Volume'] = pieces[6]
        json_quote['Adjusted Close'] = str("%.2f" % float(pieces[5]))
        if (float(pieces[4]) != float(pieces[5])):
            adjustment = float(pieces[5]) / float(pieces[4])
            json_quote['Adjusted Open'] = str("%.2f" % (float(pieces[1]) * adjustment))
            json_quote['Adjusted High'] = str("%.2f" % (float(pieces[2]) * adjustment))
            json_quote['Adjusted Low'] = str("%.2f" % (float(pieces[3]) * adjustment))
        return json_quote, interval_date

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
            except:
                raise
            params['symbol'] = symbol
        elif isinstance(symbol,list):
            # ALEX: Here add multiple-symbol retrieval from restapi with check similar to above
            symbol_data = self.symbol_reader.get_symbols(symbol)
            upper_case_symbol = [x.upper() for x in symbol]
            symbol = upper_case_symbol
            params['symbol'] = ','.join(symbol)
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

    def quote(self,symbol,interval=1,**kwargs):
        # Interval results:
        # 
        # 1 minute intervals: 2 weeks
        # 5, [15], 30, or 60 minute intervals: 10 weeks ( [##] = disabled)
        #
        data = {
            'interval': str(interval) + 'min',
            'outputsize': 'full',
            'symbol': str(symbol).upper()
        }
        response = self.request('TIME_SERIES_INTRADAY',data)
        return response
