# Core procedures for MongoDB

import json, requests

from olympus import CLIENT_CERT, RESTAPI_SERVICE, USER, User

RESTAPI_URL = 'https://zeus:4443/'

class Connection(User):

    def __init__(self,username=USER):
        super(Connection,self).__init__(username)
        self.username = username

    def connect(self):
        password = self.get_service_password(RESTAPI_SERVICE)
        data = json.dumps({ 'username': self.username, 'password': password })
        response = requests.post(
            RESTAPI_URL+'auth/login',
            cert=CLIENT_CERT,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(data))
                }
        )
        content = json.loads(response.content)
        print(content)
        if (content['message'] != 'Login successful.'):
            raise Exception('Restapi connection failed: ' + content['message'])
        self.access_token = content['access_token']
        self.refresh_token = content['refresh_token']
