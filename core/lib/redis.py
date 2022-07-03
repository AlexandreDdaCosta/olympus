# Core procedures for connection to redis

import redis

from olympus import REDIS_SERVICE, USER, User

class Connection(User):

    def __init__(self,username=USER):
        super(Connection,self).__init__(username)
        self.username = username

    def client(self):
        redis_password = self.get_service_password(REDIS_SERVICE)
        r = redis.Redis()
        redis_client = r.from_url('redis://' + self.username + ':' + redis_password + '@localhost:6379/0',decode_responses=True)
        return redis_client
