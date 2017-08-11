import datetime, pymongo, os, socket

from olympus import CAFILE, CERTFILE, KEYFILE, MONGO_URL
from olympus.projects.ploutos import DOWNLOAD_DIR, USER

DATABASE = USER

# Collections

OPTIONS_COLLECTION = 'options'
SYMBOL_COLLECTIONS_PREFIX = 'symbol_'

class Connection():
    def __init__(self,**kwargs):
        self.client = pymongo.MongoClient(MONGO_URL,ssl=True,ssl_ca_certs=CAFILE,ssl_certfile=CERTFILE,ssl_keyfile=KEYFILE)
        self.db = self.client.ploutos
        self.init_collection = self.db.init
        try:
            os.makedirs(DOWNLOAD_DIR)
        except OSError:
            pass

    def _initialized(self,init_type):
        dbnames = self.client.database_names()
        if DATABASE not in dbnames:
            return None
        else:
            cursor = self.init_collection.find({"datatype":init_type})
            if cursor.count() == 0:
                return None
            start = None
            host = None
            for init_entry in self.init_collection.find({"datatype":init_type}):
                if start is None or init_entry['start'] < start:
                    start = init_entry['start']
                    host = init_entry['host']
            return host

    def _record_start(self,init_type):
        print('Create document to record initialization.')
        dbnames = self.client.database_names()
        if self.force is True:
            self.init_collection.delete_many({"datatype":init_type})
        host = self._initialized(init_type)
        if host is None or self.force is True:
            init_record = {"host":socket.gethostname(),"start":datetime.datetime.utcnow(),"datatype":init_type}
            self.init_collection.insert_one(init_record)
        elif host != socket.gethostname():
            print('Already initialized by host '+host)
            return False
        # Check for race condition: two or more servers initializing at same time
        print('Checking for multiple init processes')
        start = None
        host = None
        for init_entry in self.init_collection.find({"datatype":init_type}):
            if start is None or init_entry['start'] < start:
                start = init_entry['start']
                host = init_entry['host']
        if host != socket.gethostname():
            # Other host got there first. Remove entry, exit initialization.
            self.db.init.delete_many({'hostname':socket.gethostname(),"datatype":init_type})
            return False
        return True
