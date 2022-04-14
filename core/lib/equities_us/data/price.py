import collections, datetime, json, re, urllib.request, wget

from datetime import datetime as dt
from datetime import timedelta
from dateutil.parser import parse
from pytz import timezone

from olympus import DOWNLOAD_DIR, USER

import olympus.equities_us.data as data

ALPHAVANTAGE_API_KEY = 'CHLVRDAEA445JOCB'
ALPHAVANTAGE_URL = 'https://www.alphavantage.co/query?apikey=' + ALPHAVANTAGE_API_KEY
YAHOO_FINANCE_URL = 'https://query1.finance.yahoo.com/v7/finance/download/'

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
            url = YAHOO_FINANCE_URL + str(symbol) + '?period1=0&period2=9999999999&interval=1d&events=history&includeAdjustedClose=true'
            target_file = DOWNLOAD_DIR(self.user)+str(symbol)+'-daily.csv'
            response = urllib.request.urlretrieve(url,target_file)
            # Verify retrieved csv

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

    def latest(self,symbol,**kwargs):
        # Complete price quote for latest trading day
        url = ALPHAVANTAGE_URL + '&function=GLOBAL_QUOTE&symbol=' + symbol
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
