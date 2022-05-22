import json, jsonschema, os, re, subprocess, time
from jsonschema import validate

import olympus.securities.equities.data as data

from olympus import USER

JSON_FILE_SUFFIX = '-companylist.json'
NORMALIZE_CAP_REGEX = re.compile('[^0-9\.]')
SYMBOL_COLLECTION = 'symbols'
SYMBOL_DATA_URLS = [
{'exchange':'amex','url':'https://api.nasdaq.com/api/screener/stocks?exchange=amex&download=true'},
{'exchange':'nasdaq','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nasdaq&download=true'},
{'exchange':'nyse','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nyse&download=true'}
]
SYMBOL_SCHEMA_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/nasdaqSymbolList.json'

class InitSymbols(data.Initializer):

    def __init__(self,username=USER,**kwargs):
        super(InitSymbols,self).__init__(SYMBOL_COLLECTION,username,**kwargs)

    def populate_collections(self):
        self.prepare()
        if self.verbose:
            print('Downloading company data.')
        company_files = []
        epoch_time = int(time.time())
        for urlconf in SYMBOL_DATA_URLS:
            target_file = urlconf['exchange']+JSON_FILE_SUFFIX
            company_files.insert(0,target_file)
            target_file = self.download_directory+target_file
            # Download site issues; use existing downloads if not too old
            if os.path.isfile(target_file) and os.stat(target_file).st_size > 1:
                if epoch_time - os.stat(target_file).st_mtime < 28800:
                    print('Using existing company list for ' + urlconf['exchange'] + ': Less than eight hours old.')
                    continue
            if self.verbose:
                print('Downloading data for exchange ' + urlconf['exchange'] + ', URL ' + urlconf['url'])
            try:
                os.remove(target_file)
            except OSError:
                pass
            try:
                # None of the python options works, even when specifying user-agent
                subprocess.run(['wget "'+urlconf['url']+'" --timeout=10 --user-agent=' + self.username + ' --output-document='+target_file], shell=True)
            except Exception as e:
                self.clean_up()
                raise

        if self.verbose:
            print('Creating unified symbol collection.')
        collection = self.db[SYMBOL_COLLECTION]
        collection.drop()

        if self.verbose:
            print('Verifying and importing downloaded data.')
        try:
            with open(SYMBOL_SCHEMA_FILE) as schema_file:
                validation_schema = json.load(schema_file)
        except:
            self.clean_up()
            raise
        for company_file in company_files:
            exchange = company_file.rstrip(JSON_FILE_SUFFIX)
            if self.verbose:
                print('Verifying data for exchange "' + exchange + '".')
            data_file_name = self.download_directory+exchange+JSON_FILE_SUFFIX
            json_data = ''
            try:
                with open(data_file_name) as data_file:
                    json_data = json.load(data_file)
                    data_file.close()
                    validate(instance=json_data,schema=validation_schema)
            except:
                self.clean_up()
                raise
            if self.verbose:
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
                self.clean_up()
                raise

        if self.verbose:
            print('Indexing updated collection.')
        try:
            if self.verbose:
                print('Indexing "Symbol".')
            collection.create_index("Symbol")
            if self.verbose:
                print('Indexing "Sector".')
            collection.create_index("Sector")
            if self.verbose:
                print('Indexing "Industry".')
            collection.create_index("Industry")
            if self.verbose:
                print('Indexing "Capitalization".')
            collection.create_index("Capitalization")
        except:
            self.clean_up()
            raise

        self.clean_up()

class Read(data.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Read,self).__init__(username,**kwargs)
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
