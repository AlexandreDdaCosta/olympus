# Core procedures for MongoDB

import json, requests

from olympus import RESTAPI_SERVICE, USER, User

RESTAPI_URL = 'https://zeus:4443/'

class Connection(User):

    def __init__(self,username=USER):
        super(Connection,self).__init__(username)
        self.username = username

    def connect(self):
        password = self.get_service_password(RESTAPI_SERVICE)
        data = json.dumps({ 'username': self.username, 'password': password })
        '''
        response = requests.post(
            RESTAPI_URL+'auth/login',
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(data))
                }
        )
        '''
        response = requests.get('https://zeus:4443/', cert='/etc/ssl/localcerts/client-key-crt.pem')
        print('RESPONSE '+str(response.content))
