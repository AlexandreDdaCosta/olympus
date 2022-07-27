import fcntl, json, time

import olympus.restapi as restapi

from olympus import USER

class Connection(restapi.Connection):

    def __init__(self,provider_name,username=USER,**kwargs):
        super(Connection,self).__init__(username,**kwargs)
        self.provider = provider_name
        self.verbose = kwargs.get('verbose',False)
        self.provider_lockfile = self.lockfile_directory()+'token.'+provider_name+'.pid'

    def access_key(self):
        # 1. Current object instance has valid api key?
        if (hasattr(self,'token') and hasattr(self,'expiration') and int(self.expiration) < int(time.time()) + 30):
            return self.token
        # 2. Current and valid access token in redis?
        redis_client = self.client()
        redis_stored_tokens = redis_client.hgetall('user:' + self.username + ':equities:token:' + self.provider)
        if redis_stored_tokens is not None:
            if ('expiration' in redis_stored_tokens and int(redis_stored_tokens['expiration']) > int(time.time()) + 30):
                self.token = redis_stored_tokens['token']
                self.expiration = redis_stored_tokens['expiration']
                return self.token
        # 3. Refresh/create via restapi query
        lockfilehandle = self._provider_token_lock()
        redis_stored_tokens = redis_client.hgetall('user:' + self.username + ':equities:token:' + self.provider)
        if redis_stored_tokens is not None:
            if ('expiration' in redis_stored_tokens and int(redis_stored_tokens['expiration']) > int(time.time()) + 30):
                for key in redis_stored_tokens:
                    if (key == 'dataSource' or key == 'message'):
                        continue
                    setattr(self,key,redis_stored_tokens[key])
                lockfilehandle.close()
                return self.token
        response = self.call('/token/equities/' + self.provider + '/')
        content = json.loads(response.content)
        if (response.status_code != 200):
            lockfilehandle.close()
            raise Exception('Restapi connection failed: ' + content['message'])
        key_found = False
        for key in content:
            if (key == 'dataSource' or key == 'message'):
                continue
            if (key == 'expiration'):
                key_found = True
            redis_client.hset('user:' + self.username + ':equities:token' + self.provider, key, content[key])
            setattr(self,key,content[key])
        if (not key_found):
            # Set a one-week default expiration if none defined
            redis_client.hset('user:' + self.username + ':equities:token' + self.provider, 'expiration', int(time.time()) + 604800)
            setattr(self,'expiration',int(time.time()) + 604800)
        lockfilehandle.close()
        return self.token

    def _provider_token_lock(self):
        for i in range(5):
            try:
                lockfilehandle = open(self.provider_lockfile,'w')
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