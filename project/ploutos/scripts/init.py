#!/usr/bin/env python3

import csv, datetime, fcntl, json, os, pymongo, socket, wget

CAFILE = '/usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt'
CERTFILE = '/etc/ssl/localcerts/client-crt.pem'
KEYFILE = '/etc/ssl/localcerts/client-key.pem'
URL = 'mongodb://zeus:27017/?ssl=true';

DATABASE= 'ploutos'
#DATADIR= '/home/ploutos/Downloads'
DATADIR= '/home/alex/Downloads'
LOCKFILE = '/var/run/olympus/projects/ploutos/init.pid'

COMPANY_DATA_URLS = [
{'exchange':'amex','url':'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=amex&render=download'},
{'exchange':'nasdaq','url':'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download'},
{'exchange':'nyse','url':'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download'}
]
OPTIONS_DATA_URL = 'http://www.cboe.com/publish/scheduledtask/mktdata/cboesymboldir2.csv'

class InitProject():

    def __init__(self,**kwargs):
        self.client = pymongo.MongoClient(URL,ssl=True,ssl_ca_certs=CAFILE,ssl_certfile=CERTFILE,ssl_keyfile=KEYFILE)
        self.db = self.client.ploutos
        self.collection = self.db.init

    def build_collections(self):
        if self.initialized() != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record end of initialization.')

        print('Retrieving foundational data sets.')
        for urlconf in COMPANY_DATA_URLS:
            target_filename = DATADIR+'/'+urlconf['exchange']+'-companylist.csv'
            try:
                os.remove(target_filename)
            except OSError:
                pass
            filename = wget.download(urlconf['url'],out=DATADIR)
            os.rename(filename,target_filename)
        target_filename = DATADIR+'/'+'cboesymboldir.csv'
        try:
            os.remove(target_filename)
        except OSError:
            pass
        filename = wget.download(OPTIONS_DATA_URL,out=DATADIR)
        os.rename(filename,target_filename)

        print('Initializing collections.')

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

    def record_start(self):
        print('Create document to record initialization.')
        dbnames = self.client.database_names()
        host = self.initialized();
        if host is None:
            init_record = {"host":socket.gethostname(),"start":datetime.datetime.utcnow()}
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
    Init.build_collections()
