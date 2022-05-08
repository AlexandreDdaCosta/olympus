import datetime, pymongo, os, socket

from olympus import MONGO_URL, USER, DOWNLOAD_DIR

DATABASE = 'equities'
INDEX_SUFFIX = '_idx'
URLS = {
   "ALPHAVANTAGE": "https://www.alphavantage.co/query?apikey=",
   "YAHOO_FINANCE": "https://query1.finance.yahoo.com/v7/finance/download/",
   "TD_AMERITRADE": "https://api.tdameritrade.com/v1/"
}

# Collections

class Connection():

    def __init__(self,user=USER,init_type=None,**kwargs):
        self.user = user
        self.verbose = kwargs.get('verbose',False)
        self.database = DATABASE
        if self.verbose is True:
            print('Establishing MongoDB client.')
        self.client = pymongo.MongoClient(MONGO_URL)
        self.db = self.client.equities
        self.init_type = init_type
        if self.init_type is not None:
            try:
                os.makedirs(DOWNLOAD_DIR(self.user))
            except OSError:
                pass
