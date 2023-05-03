# Core procedures for connection to redis

import fcntl
import redis

from olympus import REDIS_SERVICE, USER, User


class Connection(User):

    def __init__(self, username=USER):
        super(Connection, self).__init__(username)
        self.username = username

    def client(self):
        redis_password = self.get_service_password(REDIS_SERVICE)
        r = redis.Redis()
        redis_client = r.from_url('redis://' +
                                  self.username +
                                  ':' +
                                  redis_password +
                                  '@localhost:6379/0',
                                  decode_responses=True)
        return redis_client

    def _lock(self, filename):
        for i in range(5):
            try:
                lockfilehandle = open(filename, 'w')
                fcntl.flock(lockfilehandle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as e:
                if (i == 4):
                    # Last iteration
                    raise
                else:
                    time.sleep(5)
        return lockfilehandle
