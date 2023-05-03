import json
import re

from urllib.request import Request, urlopen

import olympus.securities.equities.data.provider as provider

from olympus import USER
from olympus.securities.equities.data import REQUEST_TIMEOUT


class Connection(provider.Connection):

    def __init__(self, username=USER, **kwargs):
        super(Connection, self).__init__('TDAmeritrade', username, **kwargs)

    def request(self, endpoint, params=None, method='GET', **kwargs):
        with_apikey = kwargs.get('with_apikey', True)
        token = self.access_key()
        url = self.protocol + '://' + self.url + '/v1/' + endpoint
        if with_apikey or params is not None:
            first_param = True
            if with_apikey:
                url += '?apikey=' + self.clientid
                first_param = False
            for param in params:
                if first_param is True:
                    url += '?'
                    first_param = False
                else:
                    url += '&'
                url += param + '=' + str(params[param])
        request = Request(url)
        request.add_header('Authorization', 'Bearer '+token)
        response = urlopen(request, timeout=REQUEST_TIMEOUT)
        if response.status != 200:
            raise Exception('Failed query to Ameritrade, URL ' +
                            url +
                            ': ' +
                            str(response.status))
        reply = json.loads(re.sub(r'^\s*?\/\/\s*',
                                  r'',
                                  response.read().decode("utf-8")))
        return reply
