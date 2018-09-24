import datetime, pymongo, os, socket

from olympus import CAFILE, CERTFILE, KEYFILE, MONGO_URL
from olympus.projects.ploutos import DOWNLOAD_DIR, USER

DATABASE = USER
INDEX_SUFFIX = '_idx'

# Collections

class Connection():
    def __init__(self,init_type=None,**kwargs):
        self.init_type = init_type
        self.client = pymongo.MongoClient(MONGO_URL,ssl=True,ssl_ca_certs=CAFILE,ssl_certfile=CERTFILE,ssl_keyfile=KEYFILE,ssl_match_hostname=False)
        self.db = self.client.ploutos
        self.init_collection = self.db.init
        try:
            os.makedirs(DOWNLOAD_DIR)
        except OSError:
            pass

    def _initialized(self):
        if self.init_type is None:
            raise Exception('Initialization not available for this data type; exiting.')
        dbnames = self.client.database_names()
        if DATABASE not in dbnames:
            return None
        else:
            cursor = self.init_collection.find({"datatype":self.init_type})
            if cursor.count() == 0:
                return None
            start = None
            host = None
            for init_entry in self.init_collection.find({"datatype":self.init_type}):
                if 'start' in init_entry:
                    if start is None or init_entry['start'] < start:
                        start = init_entry['start']
                        host = init_entry['host']
            return host

    def _record_start(self):
        if self.init_type is None:
            raise Exception('Initialization not available for this data type; exiting.')
        print('Create document to record initialization.')
        dbnames = self.client.database_names()
        if self.force is True:
            self.init_collection.delete_many({"datatype":self.init_type})
        host = self._initialized()
        if host is None or self.force is True:
            init_record = {"host":socket.gethostname(),"start":datetime.datetime.utcnow(),"datatype":self.init_type}
            self.init_collection.insert_one(init_record)
        elif host != socket.gethostname():
            print('Already initialized by host '+host)
            return False
        # Check for race condition: two or more servers initializing at same time
        print('Checking for multiple init processes')
        start = None
        host = None
        for init_entry in self.init_collection.find({"datatype":self.init_type}):
            if start is None or init_entry['start'] < start:
                start = init_entry['start']
                host = init_entry['host']
        if host != socket.gethostname():
            # Other host got there first. Remove entry, exit initialization.
            self.db.init.delete_many({'hostname':socket.gethostname(),"datatype":self.init_type})
            return False
        return True
