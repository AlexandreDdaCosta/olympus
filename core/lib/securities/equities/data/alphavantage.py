import json, re

from urllib.request import urlopen

import olympus.securities.equities.data.provider as provider

from olympus import USER
from olympus.securities.equities.data import REQUEST_TIMEOUT

class Connection(provider.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Connection,self).__init__('AlphaVantage',username,**kwargs)

    def request(self,function,data=None):
        token = self.access_key()
        url = self.protocol + '://' + self.url + token + '&function=' + function
        if (data is not None):
            for key in data:
                url += '&' + key + '=' + str(data[key])
        request = urlopen(url, timeout=REQUEST_TIMEOUT)
        response = json.loads(re.sub(r'^\s*?\/\/\s*',r'',request.read().decode("utf-8")))
        return response
