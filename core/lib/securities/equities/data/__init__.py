import os

import olympus.mongodb as mongodb

from olympus import USER, DOWNLOAD_DIR

DATABASE = 'equities'
INDEX_SUFFIX = '_idx'
URLS = {
   "ALPHAVANTAGE": "https://www.alphavantage.co/query?apikey=",
   "YAHOO_FINANCE": "https://query1.finance.yahoo.com/v7/finance/download/",
   "TD_AMERITRADE": "https://api.tdameritrade.com/v1/"
}

# Collections

class Connection():

    def __init__(self,user=USER,data_type=None,**kwargs):
        self.user = user
        self.verbose = kwargs.get('verbose',False)
        self.database = DATABASE
        if self.verbose is True:
            print('Establishing MongoDB client.')
        connector = mongodb.Connection(self.user)
        self.client = connector.connect()
        self.db = self.client.equities
        self.data_type = data_type
        if self.data_type is not None:
            try:
                os.makedirs(DOWNLOAD_DIR(self.user))
            except OSError:
                pass
