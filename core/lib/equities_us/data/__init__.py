import datetime, pymongo, os, socket

from olympus import CAFILE, CERTFILE, KEYFILE, MONGO_URL, USER, DOWNLOAD_DIR

DATABASE = 'equities_us'
INDEX_SUFFIX = '_idx'

# Collections

class Connection():

    def __init__(self,user=USER,init_type=None,**kwargs):
        self.user = user
        self.database = DATABASE
        self.client = pymongo.MongoClient(MONGO_URL,ssl=True,ssl_ca_certs=CAFILE,ssl_certfile=CERTFILE,ssl_keyfile=KEYFILE,ssl_match_hostname=False)
        self.db = self.client.equities_us
        self.init_type = init_type
        if self.init_type is not None:
            self.init_collection = self.db.init
            try:
                os.makedirs(DOWNLOAD_DIR(self.user))
            except OSError:
                pass
    
    def _initialized(self,**kwargs):
        if self.init_type is None:
            raise Exception('Initialization not available; exiting.')
        dbnames = self.client.database_names()
        if self.database not in dbnames:
            return None, None
        else:
            querydict = {"datatype":self.init_type}
            for key in kwargs:
                querydict[key] = kwargs[key]
            cursor = self.init_collection.find(querydict)
            if cursor.count() == 0:
                return None, None
            start = None
            host = None
            pid = None
            for init_entry in self.init_collection.find(querydict):
                if 'start' in init_entry:
                    if start is None or init_entry['start'] < start:
                        host = init_entry['host']
                        pid = init_entry['pid']
                        start = init_entry['start']
            return host, pid

    def _record_end(self,**kwargs):
        if self.init_type is None:
            raise Exception('Initialization not available; exiting.')
        host, pid = self._initialized(**kwargs)
        if host == socket.gethostname() and pid == os.getpid():
            deletedict = {"datatype":self.init_type}
            for key in kwargs:
                deletedict[key] = kwargs[key]
            self.init_collection.delete_many(deletedict)
            return True
        raise Exception('Attempt to end initialization for data type without having recorded the beginning; exiting.')

    def _record_start(self,**kwargs):
        if self.init_type is None:
            raise Exception('Initialization not available; exiting.')
        print('Creating document to record initialization.')
        dbnames = self.client.database_names()
        if self.force is True:
            querydict = {"datatype":self.init_type}
            for key in kwargs:
                querydict[key] = kwargs[key]
            self.init_collection.delete_many(querydict)
        host, pid = self._initialized(**kwargs)
        if host is None or self.force is True:
            init_record = {"host":socket.gethostname(),"pid":os.getpid(),"start":datetime.datetime.utcnow(),"datatype":self.init_type}
            for key in kwargs:
                init_record[key] = kwargs[key]
            self.init_collection.insert_one(init_record)
        elif host != socket.gethostname():
            print('Already initialized by host '+host)
            return False
        elif pid != os.getpid():
            print('Already initialized by pid '+str(pid)+' on localhost')
            return False
        # Check for race condition: two or more servers/processes initializing at same time
        print('Checking for multiple init processes')
        host, pid = self._initialized(**kwargs)
        if host != socket.gethostname() or pid != os.getpid():
            # Other host/pid got there first. Remove entry, exit initialization.
            deletedict = {'hostname':socket.gethostname(),"pid":os.getpid(),"datatype":self.init_type}
            for key in kwargs:
                deletedict[key] = kwargs[key]
            self.db.init.delete_many(deletedict)
            return False
        return True
