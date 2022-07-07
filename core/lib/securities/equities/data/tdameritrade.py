import fcntl, os

import olympus.restapi as restapi

from olympus import USER

DATABASE = 'equities'
URL = 'https://www.alphavantage.co/query?apikey='

# Collections

class Connection(restapi.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Connection,self).__init__(username)
        self.verbose = kwargs.get('verbose',False)

    def request(self,endpoint,method='get',data=None):
        pass
