#!/usr/bin/env python3

import csv, datetime, fcntl, json, os, pymongo, re, shutil, socket, wget

CAFILE = '/usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt'
CERTFILE = '/etc/ssl/localcerts/client-crt.pem'
KEYFILE = '/etc/ssl/localcerts/client-key.pem'
URL = 'mongodb://zeus:27017/?ssl=true';

#WORKINGDIR = '/home/ploutos/'
WORKINGDIR = '/tmp/'

DATABASE = 'ploutos'
DATADIR = WORKINGDIR+'Downloads/'
#LOCKFILE = '/var/run/olympus/projects/ploutos/init.pid'
LOCKFILE = '/tmp/init.pid'

NORMALIZE_CAP_REGEX = re.compile('[^0-9\.]')
SYMBOL_COLLECTION_PREFIX = 'symbol_'
OPTIONS_COLLECTION = 'options'

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
        try:
            os.makedirs(DATADIR)
        except OSError:
            pass

    def build_collections(self):
        if self.initialized() != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record end of initialization.')

        print('Retrieving foundational data sets.')

        # company files

        company_files = []
        for urlconf in COMPANY_DATA_URLS:
            target_file = urlconf['exchange']+'-companylist.csv'
            company_files.insert(0,target_file)
            target_file = DATADIR+target_file
            try:
                os.remove(target_file)
            except OSError:
                pass
            filename = wget.download(urlconf['url'],out=DATADIR)
            os.rename(filename,target_file)

        # options file

        option_file = DATADIR+'cboesymboldir.csv'
        try:
            os.remove(option_file)
        except OSError:
            pass
        filename = wget.download(OPTIONS_DATA_URL,out=DATADIR)
        os.rename(filename,option_file)

        print('\nCleaning up received csv files.')

        # company_files

        fieldnames = ["Symbol","Name","Last","Capitalization","IPO Year","Sector","Industry","Summary"]
        for company_file in company_files:
            repaired_csvfile = open(WORKINGDIR+company_file+'.import','w+')
            csvfile = open(DATADIR+company_file,'r')
            first_line = csvfile.readline().rstrip(',\n')
            for line in csvfile:
                symbol = line.split(',')[0]
                if re.match(r'.*?\^',symbol) or re.match(r'.*?\.',symbol):
                    # Drop these symbols, which are currently not relevant classes of equities
                    continue
                if re.match(r'.*?ATEST',symbol):
                    # Nasdaq test symbols
                    continue
                # Strip and convert capitalization figures
                matchobj = re.match(r'^\".*?\",\".*?\",\".*?\",\"(.*?)\"',line)
                market_cap = self._normalize_market_capitalization(matchobj.group(1))
                line = re.sub(r'^(\".*?\",\".*?\",\".*?\",)(\".*?\")',r'\g<1>'+market_cap,line)
                # Strip ending commas
                line = line[:-2] + '\n'
                # Recast "n/a" for JSON
                line = line.replace('"n/a"','null')
                # Trim ending whitespace in all columns
                line = re.sub(r'\s*\"',"\"",line)
                repaired_csvfile.write(line)
            csvfile.close()
            repaired_csvfile.close()
            csvfile = open(WORKINGDIR+company_file+'.import','r')
            jsonfile = open(WORKINGDIR+company_file+'.json','w')
            jsonfile.write('[')
            reader = csv.DictReader(csvfile,fieldnames)
            for row in reader:
                for name in fieldnames:
                    if row[name] == 'null':
                        del(row[name])
                jsonstring = json.dumps(row)
                jsonfile.write('\n'+jsonstring+',')
            jsonfile.close()
            os.remove(WORKINGDIR+company_file+'.import')
            with open(WORKINGDIR+company_file+'.json','rb+') as f:
                f.seek(0,2)
                size=f.tell()
                f.truncate(size-1)
                f.close()
            jsonfile = open(WORKINGDIR+company_file+'.json','a')
            jsonfile.write('\n]')
            jsonfile.close()

        # options_file
        
        fieldnames = ["Name","Symbol","Primary Market","Cycle","Traded on C2","2017","2018","2019","Product Types","Post/Station"]

        print('Initializing collections.')

        # company_files
        
        for urlconf in COMPANY_DATA_URLS:
            json_import_file = WORKINGDIR+urlconf['exchange']+'-companylist.csv.json'
            collection_name = SYMBOL_COLLECTION_PREFIX + urlconf['exchange']
            collection = self.db[collection_name]
            collection.drop()
            jsonfile = open(json_import_file,'r')
            json_data = json.loads(jsonfile.read())
            jsonfile.close()
            collection.insert_many(json_data)

        # options_file
        

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
        host = self.initialized()
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

    def _normalize_market_capitalization(self,c):
        multiplier = 1
        if re.match(r'.*?B',c):
            multiplier = 1000000000
        elif re.match(r'.*?M',c):
            multiplier = 1000000
        elif re.match(r'.*?T',c):
            multiplier = 1000000000000
        else:
            return 'null'
        c = re.sub(NORMALIZE_CAP_REGEX,r'',c)
        c = int(float(c) * multiplier)
        return '"'+str(c)+'"'

if __name__ == "__main__":
    lockfilehandle = open(LOCKFILE,'w')
    fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lockfilehandle.write(str(os.getpid()))
    os.chdir(WORKINGDIR)
    Init = InitProject()
    if Init.record_start() is True:
        print('Successfully recorded project initialization.')
    else:
        raise Exception('Project initialization detected; exiting.')
    Init.build_collections()
    lockfilehandle.write('')
