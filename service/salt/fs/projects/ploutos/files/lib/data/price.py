import json, re, urllib.request, wget

from olympus.projects.ploutos import *
import olympus.projects.ploutos.data as data

ALPHAVANTAGE_API_KEY = 'CHLVRDAEA445JOCB'
ALPHAVANTAGE_URL = 'https://www.alphavantage.co/query?apikey=' + ALPHAVANTAGE_API_KEY
GOOGLE_HISTORICAL_URL = 'https://www.google.com/finance/historical?startdate=Jan 01, 1970&output=csv&q='
GOOGLE_REALTIME_URL = 'https://www.google.com/finance/info?infotype=infoquoteall&q='

class Quote(data.Connection):

    def __init__(self,**kwargs):
        super(Quote,self).__init__(**kwargs)

    def Daily(self,symbol,verify=True,**kwargs):
        # Adjusted daily price quote series
        url = ALPHAVANTAGE_URL + '&function=TIME_SERIES_DAILY_ADJUSTED&outputsize=full&symbol=' + str(symbol)
        request = urllib.request.urlopen(url)
        json_reply = re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8"))
        if verify is False:
            return json.loads(json_reply)
        url = GOOGLE_HISTORICAL_URL + str(symbol)
        target_file = DOWNLOAD_DIR + 'daily.price.' + str(symbol)
        print(url)
        request = urllib.request.urlretrieve(url,target_file)
        print(request)
        return json.loads(json_reply)

    def DailyUnadjusted(self,symbol,**kwargs):
        pass

    def IntraDay(self,symbol,interval=1,**kwargs):
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

    def RealTime(self,symbols,**kwargs):
        # "symbols" can be a list or a string
        if isinstance(symbols,list):
            url_symbols = ",".join(symbols)
            url = GOOGLE_REALTIME_URL+url_symbols
        elif isinstance(symbols,str):
            url = GOOGLE_REALTIME_URL+symbols
        else:
            raise Exception("Variable 'symbols' must be a list or string.")
        request = urllib.request.urlopen(url)
        json_reply = re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8"))
        return json.loads(json_reply)
