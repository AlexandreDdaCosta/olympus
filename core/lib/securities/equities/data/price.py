import collections, datetime, json, re, urllib.request, wget

from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse
from pytz import timezone

from olympus import USER, User

import olympus.securities.equities.data as data
import olympus.securities.equities.data.symbols as symbols

from olympus.securities.equities.data import URLS

DAILY_PRICE_COLLECTION = 'price_daily'

class Quote(data.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Quote,self).__init__(username,**kwargs)
        self.user_object = User(username)

    def daily(self,symbol,**kwargs):
        # Daily price quote series
        symbol = symbol.upper()
        symbol_reader = symbols.Read(self.username,**kwargs)
        symbol_data = symbol_reader.get_symbol(symbol)
        regen = kwargs.get('regen',False)
        start_date = kwargs.get('start_date',None)
        end_date = kwargs.get('end_date',None)
        tz = timezone('EST')
        now = dt.now(tz)
        # First we check/update stored data to save on bandwidth
        collection = self.db[DAILY_PRICE_COLLECTION]
        symbol_db_data = collection.find_one({"Symbol":symbol})
        regenerate = False
        if regen is False and symbol_db_data is not None:
            refresh_date = symbol_db_data['Time']
            refresh_date_object = parse(refresh_date)
            # Regenerate:
            # If now is a weekday and before 4:00 PM, generated before today
            # If now is a weekday and after 4:00 PM, generated before 4:00 PM today
            # If now is a weekend day, generated before 4:00 last Friday
            weekday_no = now.weekday()
            if weekday_no < 5:
                # weekday
                midnight = "%d-%02d-%02d 00:00:00.000000-05:00" % (now.year,now.month,now.day)
                midnight_object = parse(midnight)
                four_pm = "%d-%02d-%02d 16:00:00.000000-05:00" % (now.year,now.month,now.day)
                four_pm_object = parse(four_pm)
                if now <= four_pm_object and refresh_date_object < midnight_object:
                    regenerate = True
                elif now > four_pm_object and refresh_date_object < four_pm_object:
                    regenerate = True
            else:
                # weekend
                last_friday = now - timedelta(days=(weekday_no-4))
                last_friday_string = "%d-%02d-%02d 16:00:00.000000-05:00" % (last_friday.year,last_friday.month,last_friday.day)
                last_friday_object = parse(last_friday_string)
                if refresh_date_object < last_friday_object:
                    regenerate = True
        elif symbol_db_data is None:
            regenerate  = True
        if regen is True or regenerate is True:
            url = URLS['YAHOO_FINANCE'] + str(symbol) + '?period1=0&period2=9999999999&interval=1d&events=history&includeAdjustedClose=true'
            target_file = self.user_object.download_directory()+str(symbol)+'-daily.csv'
            response = urllib.request.urlretrieve(url,target_file)
            with open(target_file,'r') as f:
                first_line = f.readline()
                # Verify retrieved csv
                if not re.match(r'^Date,Open,High,Low,Close,Adj Close,Volume',first_line):
                    raise Exception('First line of symbol daily data .csv file does not match expected format.')
                json_quotes = {}
                for line in f:
                    line = line.rstrip()
                    pieces = line.rstrip().split(',')
                    json_quote = {}
                    json_quote['open'] = str("%.2f" % float(pieces[1]))
                    json_quote['high'] = str("%.2f" % float(pieces[2]))
                    json_quote['low'] = str("%.2f" % float(pieces[3]))
                    json_quote['close'] = str("%.2f" % float(pieces[4]))
                    json_quote['adjusted close'] = str("%.2f" % float(pieces[5]))
                    json_quote['volume'] = pieces[6]
                    adjustment = float(pieces[5]) / float(pieces[4])
                    json_quote['adjusted open'] = str("%.2f" % (float(pieces[1]) * adjustment))
                    json_quote['adjusted high'] = str("%.2f" % (float(pieces[2]) * adjustment))
                    json_quote['adjusted low'] = str("%.2f" % (float(pieces[3]) * adjustment))
                    json_quotes[pieces[0]] = json_quote
                write_dict = {}
                write_dict['Symbol'] = symbol
                write_dict['Time'] = str(now)
                write_dict['Quotes'] = json_quotes
                if regen is True or symbol_db_data is not None:
                    collection.delete_many({ "Symbol":symbol })
                collection.insert_one(write_dict)
                symbol_db_data = collection.find_one({"Symbol":symbol})
        returndata = symbol_db_data['Quotes']
        if start_date is not None:
            start_date = dt.strptime(start_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") > start_date}
        if end_date is not None:
            end_date = dt.strptime(end_date,"%Y-%m-%d")
            returndata = {key: value for key, value in returndata.items() if dt.strptime(key,"%Y-%m-%d") < end_date}
        return collections.OrderedDict(sorted(returndata.items()))

    def intraday(self,symbol,interval=1,**kwargs):
        # Interval results:
        # 
        # 1: 2 weeks
        # 5, 15, 30, 60: 10 weeks
        # 
        if interval not in [1,5,15,30,60]:
            raise Exception("If specified, 'interval' must be in the set: 1, 5, 15, 30, 60.")
        url = URLS['ALPHAVANTAGE'] + 'CHLVRDAEA445JOCB' + '&function=TIME_SERIES_INTRADAY&outputsize=full&symbol=' + str(symbol) + '&interval=' + str(interval) + 'min'
        request = urllib.request.urlopen(url)
        json_reply = re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8"))
        return json.loads(json_reply)

    def latest(self,symbol,**kwargs):
        # Complete price quote for latest trading day
        url = URLS['ALPHAVANTAGE'] + 'CHLVRDAEA445JOCB' + '&function=GLOBAL_QUOTE&symbol=' + symbol
        request = urllib.request.urlopen(url)
        quote = json.loads(re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8")))
        quote = quote['Global Quote']
        latest = {}
        latest['change'] = quote['09. change']
        latest['change percent'] = quote['10. change percent']
        latest['close'] = quote['05. price']
        latest['date'] = quote['07. latest trading day']
        latest['last'] = quote['05. price']
        latest['low'] = quote['04. low']
        latest['high'] = quote['03. high']
        latest['open'] = quote['02. open']
        latest['previous'] = quote['08. previous close']
        latest['symbol'] = symbol
        latest['volume'] = quote['06. volume']
        return latest
