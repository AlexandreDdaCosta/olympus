import codecs, csv, json, jsonschema, os, re, subprocess, time
from jsonschema import validate

import olympus.restapi as restapi
import olympus.securities.equities.data as data

from olympus import USER

COMPANY_SYMBOL_SCHEMA_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/NasdaqSymbolList.json'
ETF_INDEX_DATA_FILE_NAME = 'usexchange-etf+indexlist.csv'
ETF_INDEX_DATA_URL = 'http://masterdatareports.com/Download-Files/AllTypes.csv'
ETF_INDEX_JSON_FILE_NAME = 'usexchange-etf+indexlist.json'
ETF_INDEX_SYMBOL_SCHEMA_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/ETFIndexSymbolList.json'
JSON_FILE_SUFFIX = '-companylist.json'
NASDAQ_TRADED_DATA_FILE_NAME = 'nasdaqtraded.txt'
NASDAQ_TRADED_DATA_URL = 'ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt'
NASDAQ_TRADED_JSON_FILE_NAME = 'nasdaqtraded.json'
NASDAQ_TRADED_SYMBOL_SCHEMA_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/NasdaqTradedSymbolList.json'
NORMALIZE_CAP_REGEX = re.compile('[^0-9\.]')
SYMBOL_COLLECTION = 'symbols'
SYMBOL_CORRECTIONS_CONFIG_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'config/symbol_corrections.json'
SYMBOL_DATA_URLS = [
{'exchange':'amex','url':'https://api.nasdaq.com/api/screener/stocks?exchange=amex&download=true'},
{'exchange':'nasdaq','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nasdaq&download=true'},
{'exchange':'nyse','url':'https://api.nasdaq.com/api/screener/stocks?exchange=nyse&download=true'}
]
WATCHLIST_CONFIG_FILE = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'config/symbol_watchlists.json'

class InitSymbols(data.Initializer):

    def __init__(self,username=USER,**kwargs):
        super(InitSymbols,self).__init__(SYMBOL_COLLECTION,username,**kwargs)

    def populate_collections(self):
        self.prepare()
        if self.verbose:
            print('Downloading exchange listed symbol data.')
        company_files = []
        for urlconf in SYMBOL_DATA_URLS:
            target_file = urlconf['exchange']+JSON_FILE_SUFFIX
            company_files.insert(0,target_file)
            self._download_symbol_file(target_file,urlconf['url'],'Verifying data for '+urlconf['exchange']+'.','Using existing company list for '+urlconf['exchange']+'.','Downloading data for '+urlconf['exchange']+'.')
        self._download_symbol_file(ETF_INDEX_DATA_FILE_NAME,ETF_INDEX_DATA_URL,'Verifying ETF and index data.','Using existing ETF/index list.','Downloading ETF/index list.')
        self._download_symbol_file(NASDAQ_TRADED_DATA_FILE_NAME,NASDAQ_TRADED_DATA_URL,'Verifying Nasdaq traded data.','Using existing Nasdaq traded download.','Downloading Nasdaq traded symbols list.')
    
        if self.verbose:
            print('Creating unified symbol collection.')
        collection = self.db[SYMBOL_COLLECTION]
        collection.drop()
        added_symbols = {}

        if self.verbose:
            print('Verifying and importing downloaded company symbol data.')
        try:
            with open(COMPANY_SYMBOL_SCHEMA_FILE) as schema_file:
                validation_schema = json.load(schema_file)
        except:
            self.clean_up()
            raise
        for company_file in company_files:
            exchange = company_file.rstrip(JSON_FILE_SUFFIX)
            if self.verbose:
                print('Verifying data for exchange "' + exchange + '".')
            data_file_name = self.download_directory()+exchange+JSON_FILE_SUFFIX
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
                    company['SecurityClass'] = 'Stock'
                    company['Symbol'] = company.pop('symbol')
                    added_symbols[company['Symbol']] = True
                    json_write.append(company)
                collection.insert_many(json_write)
            except:
                self.clean_up()
                raise
        if self.verbose:
            print('Verifying downloaded ETF and index symbol data.')
        try:
            with open(ETF_INDEX_SYMBOL_SCHEMA_FILE) as schema_file:
                validation_schema = json.load(schema_file)
        except:
            self.clean_up()
            raise
        # For proper conversion, modify first line of downloaded file with hash keys
        data_file_name = self.download_directory()+ETF_INDEX_DATA_FILE_NAME
        data_file_name_utf8 = self.download_directory()+ETF_INDEX_DATA_FILE_NAME+'.utf8'
        json_file_name = self.download_directory()+ETF_INDEX_JSON_FILE_NAME
        with codecs.open(data_file_name, 'r', encoding='ISO-8859-1') as f:
            lines = f.readlines()
        lines[0] = "Name,Symbol,Category,Trash\n"
        with open(data_file_name_utf8, "w") as f:
            f.writelines(lines)
        # CSV to JSON
        json_array = []
        with open(data_file_name_utf8, encoding='utf-8') as csvf: 
            csv_reader = csv.DictReader(csvf) 
            for row in csv_reader: 
                json_array.append(row)
        with open(json_file_name, 'w', encoding='utf-8') as json_file: 
            json_string = json.dumps(json_array, indent=4)
            json_file.write(json_string)
        json_data = ''
        try:
            with open(json_file_name) as json_file:
                json_data = json.load(json_file)
                validate(instance=json_data,schema=validation_schema)
        except:
            self.clean_up()
            raise

        if self.verbose:
            print('Importing ETF/index symbol data.')
        try:
            json_write = []
            for entry in json_data:
                entry.pop('Trash',None)
                if (re.search("Index", entry['Category'])):
                    entry['SecurityClass'] = 'Index'
                    entry['OriginalSymbol'] = entry.pop('Symbol')
                    entry['Symbol'] = re.sub("^\.", "", entry['OriginalSymbol'])
                else:
                    entry['SecurityClass'] = 'ETF'
                if entry['Symbol'] in added_symbols:
                    continue
                added_symbols[entry['Symbol']] = True
                json_write.append(entry)
            collection.insert_many(json_write)
        except:
            self.clean_up()
            raise

        if self.verbose:
            print('Verifying downloaded Nasdaq traded symbol data.')
        try:
            with open(NASDAQ_TRADED_SYMBOL_SCHEMA_FILE) as schema_file:
                validation_schema = json.load(schema_file)
        except:
            self.clean_up()
            raise

        data_file_name = self.download_directory() + NASDAQ_TRADED_DATA_FILE_NAME
        json_file_name = self.download_directory() + NASDAQ_TRADED_JSON_FILE_NAME
        # CSV to JSON
        json_array = []
        with open(data_file_name, encoding='utf-8') as csvf: 
            csv_reader = csv.DictReader(csvf,delimiter = "|") 
            for row in csv_reader:
                if re.match('.*[.$].*',row['Symbol']):
                    continue
                if not row['Symbol']:
                    continue
                if row['Symbol'] in added_symbols:
                    continue
                if row['Test Issue'] == 'Y':
                    continue
                added_symbols[row['Symbol']] = True
                json_array.append(row)
        with open(json_file_name, 'w', encoding='utf-8') as json_file: 
            json_string = json.dumps(json_array, indent=4)
            json_file.write(json_string)
        json_data = ''
        try:
            with open(json_file_name) as json_file:
                json_data = json.load(json_file)
                validate(instance=json_data,schema=validation_schema)
        except:
            self.clean_up()
            raise

        if self.verbose:
            print('Importing Nasdaq traded symbol data.')
        try:
            json_write = []
            for entry in json_data:
                entry.pop('CQS Symbol')
                entry.pop('Financial Status')
                entry.pop('Market Category')
                entry.pop('Nasdaq Traded')
                entry.pop('NextShares')
                entry.pop('Round Lot Size')
                entry.pop('Symbol')
                entry.pop('Test Issue')
                entry['Exchange'] = entry.pop('Listing Exchange')
                entry['Name'] = entry.pop('Security Name')
                entry['Symbol'] = entry.pop('NASDAQ Symbol')
                if entry.pop('ETF') == 'Y':
                    entry['SecurityClass'] = 'ETF'
                else:
                    entry['SecurityClass'] = 'Stock'
                json_write.append(entry)
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

    def post_populate_collections(self):
        if self.verbose:
            print('Modifying stored symbol collections via configuration files.')
        collection = self.db[SYMBOL_COLLECTION]
        unknown_symbols = []
        # Symbol details
        if os.path.isfile(SYMBOL_CORRECTIONS_CONFIG_FILE):
            with open(SYMBOL_CORRECTIONS_CONFIG_FILE) as corrections_file:
                corrections = json.load(corrections_file)
            for symbol in corrections:
                if (corrections[symbol]['Action'] == 'update'):
                    existing_symbol=collection.find_one({ "Symbol": symbol, "SecurityClass": corrections[symbol]['SecurityClass'] })
                    if existing_symbol is None:
                        unknown_symbols.append(symbol)
                        continue
                    recid = collection.update_one({ "Symbol": symbol, "SecurityClass": corrections[symbol]['SecurityClass'] },{ "$set": corrections[symbol]['What'] })
                else:
                    raise Exception('Unknown operation ' + corrections[symbol]['Action'] + ' requested during symbol post population.')
        # Watchlists
        if os.path.isfile(WATCHLIST_CONFIG_FILE):
            with open(WATCHLIST_CONFIG_FILE) as watchlist_file:
                watchlists = json.load(watchlist_file)
            for watchlist_name in watchlists:
                existing_watchlist_symbols=collection.find({ "Watchlists": watchlist_name })
                for watchlist_symbol in existing_watchlist_symbols:
                    if (watchlist_symbol['Symbol'] in watchlists[watchlist_name]):
                        watchlists[watchlist_name].remove(watchlist_symbol['Symbol'])
                    else:
                        symbol_watchlists = watchlist_symbol['Watchlists']
                        symbol_watchlists.remove(watchlist_name)
                        collection.update_one({ "Symbol": watchlist_symbol['Symbol'] }, { "$set": { "Watchlists": symbol_watchlists } })
                for symbol in watchlists[watchlist_name]:
                    existing_symbol=collection.find_one({ "Symbol": symbol })
                    if existing_symbol is None:
                        unknown_symbols.append(symbol)
                        continue
                    if 'Watchlists' not in existing_symbol:
                        symbol_watchlists = [ watchlist_name ]
                    else:
                        symbol_watchlists = existing_symbol['Watchlists']
                        symbol_watchlists.append(watchlist_name)
                    collection.update_one({ "Symbol": symbol }, { "$set": { "Watchlists": symbol_watchlists } })
        if unknown_symbols:
            raise Exception('Unknown symbols detected during post population: '+str(unknown_symbols))

    def _download_symbol_file(self,target_file,url,verbose_title,verbose_nodownload,verbose_download_symbol_file):
        if self.verbose:
            print(verbose_title)
        epoch_time = int(time.time())
        target_file = self.download_directory() + target_file
        # Use existing downloads if less than eight hours old
        if os.path.isfile(target_file) and os.stat(target_file).st_size > 1:
            if epoch_time - os.stat(target_file).st_mtime < 28800:
                print(verbose_nodownload)
                return
        if self.verbose:
            print(verbose_download_symbol_file)
        try:
            os.remove(target_file)
        except OSError:
            pass
        try:
            subprocess.run(['wget "' + url + '" --timeout=10 --user-agent=' + self.username + ' --output-document='+target_file], shell=True)
            subprocess.run(['touch '+target_file], shell=True)
        except Exception as e:
            self.clean_up()
            raise

class Read(restapi.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Read,self).__init__(username,**kwargs)

    def get_symbol(self,symbol,**kwargs):
        symbol = symbol.upper()
        response = self.call('/equities/symbol/'+symbol)
        if (response.status_code == 404):
           raise SymbolNotFoundError(symbol)
        content = json.loads(response.content)
        return content['symbol']

    def get_symbols(self,symbols,**kwargs):
        symbol_string = ','.join([symbol.upper() for symbol in symbols])
        response = self.call('/equities/symbols/'+symbol_string)
        content = json.loads(response.content)
        return content

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
