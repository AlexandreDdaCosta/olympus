import json, re, urllib.request, wget

import datetime

from datetime import datetime as dt
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
        tz = timezone('EST')
        now = dt.now(tz)
        # First we check/update stored data to save on bandwidth
        collection = self.db[DAILY_PRICE_COLLECTION]
        symbol_db_data = collection.find_one({"Symbol":symbol})
        if symbol_db_data is not None:
            refresh_date = symbol_db_data['Time']
            # Regenerate:
            # If now is a weekday and before 4:00 PM, generated before today
            # If now is a weekday and after 4:00 PM, generated before 4:00 PM today
            # If now is a weekend day, generated before 4:00 last Friday
            # ALEX
            weekday_no = now.weekday()
            if weekday_no < 5:
                # weekday
                pass
            else:
                # weekend
                pass
            die
            return symbol_db_data['Quote']['Time Series (Daily)']
        # Query API once past stored data date check
        url = ALPHAVANTAGE_URL + '&function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol=' + str(symbol)
        request = urllib.request.urlopen(url)
        raw_json_reply = re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8"))
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
            line = re.sub(r'^(\s*?\")([0-9]*\.\s+)(.*)$',r'\1\3',line)
            json_reply += line + '\n'
        write_reply = '{"Symbol":"'+symbol+'","Time":"'+str(now)+'","Quote":'+json_reply + '}'
        if symbol_db_data is not None:
            collection.delete_one({ "Symbol":symbol })
        collection.insert_one(json.loads(write_reply))
        symbol_db_data = collection.find_one({"Symbol":symbol})
        return symbol_db_data['Quote']['Time Series (Daily)']

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
