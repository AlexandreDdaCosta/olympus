#!/usr/bin/env python3

import datetime, fcntl, os, pymongo, socket

CAFILE = '/usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt'
CERTFILE = '/etc/ssl/localcerts/client-crt.pem'
KEYFILE = '/etc/ssl/localcerts/client-key.pem'
URL = 'mongodb://zeus:27017/?ssl=true';

DATABASE= 'ploutos'
LOCKFILE = '/var/run/olympus/projects/ploutos/init.pid'

COMPANY_DATA_URLS = [
{'exchange':'amex','url':'http://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=AMEX'},
{'exchange':'nasdaq','url':'http://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=NASDAQ'},
{'exchange':'nyse','url':'http://www.nasdaq.com/screening/companies-by-industry.aspx?exchange=NYSE'},
]
OPTIONS_DATA_URL = 'http://www.cboe.com/publish/scheduledtask/mktdata/cboesymboldir2.csv'

class InitProject():

    print(COMPANY_DATA_URLS)

    def __init__(self,**kwargs):
        self.client = pymongo.MongoClient(URL,ssl=True,ssl_ca_certs=CAFILE,ssl_certfile=CERTFILE,ssl_keyfile=KEYFILE)
        self.db = self.client.ploutos
        self.collection = self.db.init

    def build_collections(self):
        pass

    def get_initial_data(self):
        print('Retrieving foundational data sets.')
        if self.initialized() != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record end of initialization.')
        cursor = self.collection.find({"host":socket.gethostname()})

    def initialized(self):
        dbnames = self.client.database_names()
        if DATABASE not in dbnames:
            return None
        else:
            cursor = self.collection.find({})
            if cursor.count() == 0:
                return None
            start = None
            host = None
            for init_entry in self.collection.find({}):
                if start is None or init_entry['start'] < start:
                    start = init_entry['start']
                    host = init_entry['host']
            return host

    def record_end(self):
        print('Recording end of initialization.')
        if self.initialized() != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record end of initialization.')

    def record_start(self):
        print('Create document to record initialization.')
        dbnames = self.client.database_names()
        host = self.initialized();
        if host is None:
            init_record = {"host":socket.gethostname(),"last":None,"start":datetime.datetime.utcnow(),"end":None}
            self.collection.insert_one(init_record)
        elif host != socket.gethostname():
            print('Already initialized by host '+host)
            return False
        else:
            return True
        cursor = self.collection.find({})
        if cursor.count() != 1:
            # Check for race condition: two or more servers initializing at same time
            print('Checking for multiple init processes')
            start = None
            host = None
            for init_entry in self.collection.find({}):
                if start is None or init_entry['start'] < start:
                    start = init_entry['start']
                    host = init_entry['host']
            if host != socket.gethostname():
                # Other host got there first. Remove entry, exit initialization.
                self.db.init.delete_many({'hostname':socket.gethostname()})
                return False
        return True

if __name__ == "__main__":
    lockfilehandle = open(LOCKFILE,'w')
    fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lockfilehandle.write(str(os.getpid()))
    Init = InitProject()
    if Init.record_start() is True:
        print('Successfully recorded project initialization.')
    else:
        raise Exception('Project initialization detected; exiting.')
    Init.record_end()
