import ast, csv, datetime, fcntl, json, jsonschema, os, re, socket, subprocess, time
from jsonschema import validate

import olympus.equities_us.data as data

from olympus import USER, DOWNLOAD_DIR, LOCKFILE_DIR, WORKING_DIR

INIT_TYPE = 'symbols'
JSON_FILE_SUFFIX = '-companylist.json'
NORMALIZE_CAP_REGEX = re.compile('[^0-9\.]')
SYMBOL_COLLECTION = INIT_TYPE
SYMBOL_DATA_URLS = [
{'exchange':'amex','url':'https://api.nasdaq.com/api/screener/stocks?exchange=amex&download=true'},
{'exchange':'nasdaq','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nasdaq&download=true'},
{'exchange':'nyse','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nyse&download=true'}
]
SYMBOL_SCHEMA_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/nasdaqSymbolList.json'

class Init(data.Connection):

    def __init__(self,user=USER,**kwargs):
        super(Init,self).__init__(user,INIT_TYPE,**kwargs)
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('graceful',False)
        self.verbose = kwargs.get('verbose',False)
        self.working_dir = WORKING_DIR(self.user)

    def populate_collections(self):

        if self.verbose is True:
            print('Setting up environment.')
        LOCKFILE = LOCKFILE_DIR(self.user)+INIT_TYPE+'.pid'
        lockfilehandle = open(LOCKFILE,'w')
        fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lockfilehandle.write(str(os.getpid()))
        os.chdir(self.working_dir)
       
        if self.verbose is True:
            print('Initialization checks to prevent multiple execution.')
        if self._record_start() is not True:
            self._clean_up(lockfilehandle,False)
            if self.graceful is True:
                print('Initialization record check failed; cannot record start of initialization.')
                return
            else:
                raise Exception('Initialization record check failed; cannot record start of initialization.')
    
        if self.verbose is True:
            print('Downloading company data.')
        company_files = []
        epoch_time = int(time.time())
        for urlconf in SYMBOL_DATA_URLS:
            target_file = urlconf['exchange']+JSON_FILE_SUFFIX
            company_files.insert(0,target_file)
            target_file = DOWNLOAD_DIR(self.user)+target_file
            if self.force is False:
                # Download site issues; use existing downloads if not too old
                if os.path.isfile(target_file) and os.stat(target_file).st_size > 1:
                    if epoch_time - os.stat(target_file).st_mtime < 28800:
                        print('Using existing company list for ' + urlconf['exchange'] + ': Less than eight hours old.')
                        continue
            if self.verbose is True:
                print('Downloading data for exchange ' + urlconf['exchange'] + ', URL ' + urlconf['url'])
            try:
                os.remove(target_file)
            except OSError:
                pass
            try:
                # None of the python options works, even when specifying user-agent
                subprocess.run(['wget "'+urlconf['url']+'" --timeout=10 --user-agent=' + self.user + ' --output-document='+target_file], shell=True)
            except Exception as e:
                self._clean_up(lockfilehandle)
                if self.graceful is True:
                    print('WARNING: Bypassing initialization due to download error: '+str(e))
                    return
                raise

        if self.verbose is True:
            print('Creating unified symbol collection.')
        collection_name = SYMBOL_COLLECTION
        collection = self.db[collection_name]
        collection.drop()

        if self.verbose is True:
            print('Verifying and importing downloaded data.')
        try:
            with open(SYMBOL_SCHEMA_FILE) as schema_file:
                validation_schema = json.load(schema_file)
        except:
            self._clean_up(lockfilehandle)
            raise
        for company_file in company_files:
            exchange = company_file.rstrip(JSON_FILE_SUFFIX)
            if self.verbose is True:
                print('Verifying data for exchange "' + exchange + '".')
            data_file_name = DOWNLOAD_DIR(self.user)+exchange+JSON_FILE_SUFFIX
            json_data = ''
            try:
                with open(data_file_name) as data_file:
                    json_data = json.load(data_file)
                    data_file.close()
                    validate(instance=json_data,schema=validation_schema)
            except:
                self._clean_up(lockfilehandle)
                raise
            if self.verbose is True:
                print('Importing symbol data for exchange "' + exchange + '".')
            try:
                json_write = []
                for company in json_data['data']['rows']:
                    if company['sector'] == '':
                        continue
                    company.pop('lastsale',None)
                    company.pop('netchange',None)
                    company.pop('pctchange',None)
                    company.pop('volume',None)
                    company.pop('url',None)
                    company['Capitalization'] = company.pop('marketCap')
                    if company['Capitalization'] == '':
                        company['Capitalization'] = 0
                    else:
                        company['Capitalization'] = int(float(company['Capitalization']))
                    company['Country'] = company.pop('country')
                    company['Exchange'] = exchange
                    company['Industry'] = company.pop('industry')
                    company['IPO Year'] = company.pop('ipoyear')
                    company['Name'] = company.pop('name')
                    company['Sector'] = company.pop('sector')
                    company['Symbol'] = company.pop('symbol')
                    json_write.append(company)
                collection.insert_many(json_write)
            except:
                self._clean_up(lockfilehandle)
                raise

        if self.verbose is True:
            print('Indexing updated collection.')
        try:
            if self.verbose is True:
                print('Indexing "Symbol".')
            collection.create_index("Symbol")
            if self.verbose is True:
                print('Indexing "Sector".')
            collection.create_index("Sector")
            if self.verbose is True:
                print('Indexing "Industry".')
            collection.create_index("Industry")
            if self.verbose is True:
                print('Indexing "Capitalization".')
            collection.create_index("Capitalization")
        except:
            self._clean_up(lockfilehandle)
            raise
	
        self._clean_up(lockfilehandle)
	
    def _clean_up(self,lockfilehandle,end_it=True):
        if self.verbose is True:
            print('Cleaning up symbol creation process.')
        if end_it is True:
            self._record_end()
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

class Read(data.Connection):

    def __init__(self,**kwargs):
        super(Read,self).__init__(**kwargs)
        if SYMBOL_COLLECTION not in self.db.list_collection_names():
            raise Exception('Symbol collection "' + SYMBOL_COLLECTION + '" not located in database "' + self.database + '". Collections located: ' + str(self.db.list_collection_names()))
        self.collection = self.db[SYMBOL_COLLECTION]

    def get_symbol(self,symbol,**kwargs):
        symbol = symbol.upper()
        return self.collection.find_one({"Symbol":symbol})
