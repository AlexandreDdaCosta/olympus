import ast, csv, datetime, fcntl, json, jsonschema, os, re, socket, subprocess, time
from jsonschema import validate

import olympus.securities.equities.data as data

from olympus import USER, User

DATA_TYPE = 'symbols'
JSON_FILE_SUFFIX = '-companylist.json'
NORMALIZE_CAP_REGEX = re.compile('[^0-9\.]')
SYMBOL_COLLECTION = DATA_TYPE
SYMBOL_DATA_URLS = [
{'exchange':'amex','url':'https://api.nasdaq.com/api/screener/stocks?exchange=amex&download=true'},
{'exchange':'nasdaq','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nasdaq&download=true'},
{'exchange':'nyse','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nyse&download=true'}
]
SYMBOL_SCHEMA_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/nasdaqSymbolList.json'

class InitSymbols(data.Connection):

    def __init__(self,user=USER,**kwargs):
        super(InitSymbols,self).__init__(user,DATA_TYPE,**kwargs)
        self.verbose = kwargs.get('verbose',False)
        self.user_object = User(user)
        self.download_dir = self.user_object.download_directory()
        self.working_dir = self.user_object.working_directory()
        self.lockfile = self.user_object.lockfile_directory()+DATA_TYPE+'.pid'

    def populate_collections(self):

        if self.verbose:
            print('Setting up environment.')
        lockfilehandle = open(self.lockfile,'w')
        fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lockfilehandle.write(str(os.getpid()))
        os.chdir(self.working_dir)
       
        if self.verbose is True:
            print('Downloading company data.')
        company_files = []
        epoch_time = int(time.time())
        for urlconf in SYMBOL_DATA_URLS:
            target_file = urlconf['exchange']+JSON_FILE_SUFFIX
            company_files.insert(0,target_file)
            target_file = self.download_dir+target_file
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
            data_file_name = self.download_dir+exchange+JSON_FILE_SUFFIX
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
	
    def _clean_up(self,lockfilehandle):
        if self.verbose is True:
            print('Cleaning up symbol creation process.')
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

class Read(data.Connection):

    def __init__(self,user=USER,**kwargs):
        super(Read,self).__init__(user,**kwargs)
        if SYMBOL_COLLECTION not in self.db.list_collection_names():
            raise Exception('Symbol collection "' + SYMBOL_COLLECTION + '" not located in database "' + self.database + '". Collections located: ' + str(self.db.list_collection_names()))
        self.collection = self.db[SYMBOL_COLLECTION]

    def get_symbol(self,symbol,**kwargs):
        symbol = symbol.upper()
        result = self.collection.find_one({"Symbol":symbol})
        if result is None:
            raise SymbolNotFoundError(symbol)
        return result

class SymbolNotFoundError(Exception):
    """ Raised for non-existent symbol
    Attributes:
        symbol: Missing symbol
        message: Explanation
    """

    def __init__(self, symbol, message='Queried symbol not found in symbol database'):
        self.symbol = symbol
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message + ' : ' + self.symbol
