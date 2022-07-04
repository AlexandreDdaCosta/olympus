# Core procedures for connection to restapi back end

import fcntl, json, requests, time

from olympus import CLIENT_CERT, REDIS_SERVICE, RESTAPI_SERVICE, USER, User

import olympus.redis as redis

RESTAPI_URL = 'https://zeus:4443/'

class Connection(redis.Connection):

    def __init__(self,username=USER):
        super(Connection,self).__init__(username)
        self.username = username
        self.token_lockfile = self.lockfile_directory()+'redis.token.pid'

    def token(self):
        # 1. Current object instance has valid access token?
        if (hasattr(self,'access_token') and hasattr(self,'access_token_expiration') and self.access_token_expiration < int(time.time()) + 30):
            return self.access_token
        # 2. Current and valid access token in redis?
        redis_client = self.client()
        redis_stored_tokens = redis_client.hgetall('user:' + self.username + ':restapi:token')
        if redis_stored_tokens is not None:
            if ('access_token_expiration' in redis_stored_tokens and int(redis_stored_tokens['access_token_expiration']) > int(time.time()) + 30):
                self.access_token = redis_stored_tokens['access_token']
                self.access_token_expiration = redis_stored_tokens['access_token_expiration']
                return self.access_token;
        # 3. Current and valid refresh token in redis?
            elif ('refresh_token_expiration' in redis_stored_tokens and int(redis_stored_tokens['refresh_token_expiration']) > int(time.time()) + 30):
                refresh_token = redis_stored_tokens['refresh_token']
                # 3a.  Lock execution file
                lockfilehandle = self._token_lock()
                # 3b.  Query redis, confirm issue
                redis_stored_tokens = redis_client.hgetall('user:' + self.username + ':restapi:token')
                if redis_stored_tokens is not None:
                    if ('access_token_expiration' in redis_stored_tokens and int(redis_stored_tokens['access_token_expiration']) > int(time.time()) + 30):
                        self.access_token = redis_stored_tokens['access_token']
                        self.access_token_expiration = redis_stored_tokens['access_token_expiration']
                        lockfilehandle.close()
                        return self.access_token;
                # 3c.  Query back end
                data = json.dumps({ 'username': self.username })
                response = requests.post(
                    RESTAPI_URL+'auth/refresh',
                    cert=CLIENT_CERT,
                    data=data,
                    headers={
                        'Authorization': 'Bearer ' + refresh_token,
                        'Content-Type': 'application/json',
                        'Content-Length': str(len(data))
                        }
                )
                content = json.loads(response.content)
                if (content['message'] == 'Refresh successful.'):
                    # 3d.  Update redis with fresh settings
                    redis_client.hset('user:' + self.username + ':restapi:token', 'access_token_expiration', content['access_token_expiration'])
                    redis_client.hset('user:' + self.username + ':restapi:token', 'access_token', content['access_token'])
                    redis_client.hset('user:' + self.username + ':restapi:token', 'refresh_token_expiration', content['refresh_token_expiration'])
                    redis_client.hset('user:' + self.username + ':restapi:token', 'refresh_token', content['refresh_token'])
                else:
                    lockfilehandle.close()
                    raise Exception('Restapi connection failed: ' + content['message'])
                # 3e.  Unlock execution file
                lockfilehandle.close()

                self.access_token = content['access_token']
                self.access_token_expiration = content['access_token_expiration']
                return self.access_token;
        # 4. Fall back to username/password auth
        # 4a. Lock execution file
        lockfilehandle = self._token_lock()
        # 4b. Query redis, confirm issue
        redis_stored_tokens = redis_client.hgetall('user:' + self.username + ':restapi:token')
        if redis_stored_tokens is not None:
            if ('access_token_expiration' in redis_stored_tokens and int(redis_stored_tokens['access_token_expiration']) > int(time.time()) + 30):
                self.access_token = redis_stored_tokens['access_token']
                self.access_token_expiration = redis_stored_tokens['access_token_expiration']
                lockfilehandle.close()
                return self.access_token;
        # 4c.  Query back end
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
        if (content['message'] != 'Login successful.'):
            lockfilehandle.close()
            raise Exception('Restapi connection failed: ' + content['message'])
        # 4d.  Update redis with fresh settings
        redis_client.hset('user:' + self.username + ':restapi:token', 'access_token_expiration', content['access_token_expiration'])
        redis_client.hset('user:' + self.username + ':restapi:token', 'access_token', content['access_token'])
        redis_client.hset('user:' + self.username + ':restapi:token', 'refresh_token_expiration', content['refresh_token_expiration']) 
        redis_client.hset('user:' + self.username + ':restapi:token', 'refresh_token', content['refresh_token'])
        # 4e.  Unlock execution file
        lockfilehandle.close()

        self.access_token = content['access_token']
        self.access_token_expiration = content['access_token_expiration']
        return self.access_token;

    def _token_lock(self):
        for i in range(5):
            try:
                lockfilehandle = open(self.token_lockfile,'w')
                fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError as e:
                if (i == 4):
                    # Last iteration
                    raise
                else:
                    time.sleep(5)
            except:
                raise
        return lockfilehandle