import collections, datetime, json, re, urllib.request, wget

from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse
from pytz import timezone

from olympus import USER

import olympus.equities_us.data as data

ALPHAVANTAGE_API_KEY = 'CHLVRDAEA445JOCB'
ALPHAVANTAGE_URL = 'https://www.alphavantage.co/query?apikey=' + ALPHAVANTAGE_API_KEY
ALTERNATE_URL = 'https://api.iextrading.com'

DAILY_PRICE_COLLECTION = 'price_daily'

class Quote(data.Connection):

    def __init__(self,user=USER,**kwargs):
        super(Quote,self).__init__(user,'quote',**kwargs)

    def daily(self,symbol,**kwargs):
        # Daily price quote series
        symbol = symbol.upper()
        regen = kwargs.get('regen',False)
        start_date = kwargs.get('start_date',None)
        end_date = kwargs.get('end_date',None)
        regen = kwargs.get('regen',False)
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
                regenerate = True
            else:
                # weekend
                last_friday = now - timedelta(days=(weekday_no-4))
                last_friday_string = "%d-%02d-%02d 16:00:00.000000-05:00" % (last_friday.year,last_friday.month,last_friday.day)
                last_friday_object = parse(last_friday_string)
                if refresh_date_object < last_friday_object:
                    regenerate = True
        if regen is True or regenerate is True:
            url = ALPHAVANTAGE_URL + '&function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol=' + str(symbol)
            request = urllib.request.urlopen(url)
            raw_json_reply = re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8"))
            json.loads(raw_json_reply) # Test for valid json
            # Clean up returned result
            json_reply = ''
            for line in raw_json_reply.splitlines():
                line = line.rstrip()
                if 'dividend amount\": \"0.0000' in line:
                    continue
                if 'split coefficient' in line:
                    json_reply = json_reply[:-2]
                    json_reply = json_reply + '\n'
                    continue
                line = re.sub(r'^\s*?(\")([0-9]*\.\s+)(.*)$',r'\1\3',line)
                json_reply += line + '\n'
            write_reply = '{"Symbol":"'+symbol+'","Time":"'+str(now)+'","Quote":'+json_reply + '}'
            if regen is True or symbol_db_data is not None:
                collection.delete_many({ "Symbol":symbol })
            collection.insert_one(json.loads(write_reply))
            symbol_db_data = collection.find_one({"Symbol":symbol})
        returndata = symbol_db_data['Quote']['Time Series (Daily)']
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
        url = ALPHAVANTAGE_URL + '&function=TIME_SERIES_INTRADAY&outputsize=full&symbol=' + str(symbol) + '&interval=' + str(interval) + 'min'
        request = urllib.request.urlopen(url)
        json_reply = re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8"))
        return json.loads(json_reply)

    def real_time(self,symbols,**kwargs):
        # "symbols" can be a list or a string
        if isinstance(symbols,list):
            url_symbols = ",".join(symbols)
            url = ALPHAVANTAGE_URL + '&function=BATCH_STOCK_QUOTES&outputsize=full&symbols=' + url_symbols
        elif isinstance(symbols,str):
            url = ALPHAVANTAGE_URL + '&function=BATCH_STOCK_QUOTES&outputsize=full&symbols=' + symbols
        else:
            raise Exception("Variable 'symbols' must be a list or string.")
        request = urllib.request.urlopen(url)
        json_reply = re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8"))
        return json.loads(json_reply)
