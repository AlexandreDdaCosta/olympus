import ast, csv, datetime, fcntl, json, os, re, socket, subprocess, time

import olympus.equities_us.data as data

from olympus import USER, DOWNLOAD_DIR, LOCKFILE_DIR, WORKING_DIR

INIT_TYPE = 'symbols'
SYMBOL_COLLECTION = INIT_TYPE
SYMBOL_DATA_URLS = [
{'exchange':'nasdaq','url':'ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt','first_line_string':'Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares'},
{'exchange':'other','url':'ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt','first_line_string':'ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol'}
]

class Init(data.Connection):

    def __init__(self,user=USER,**kwargs):
        super(Init,self).__init__(user,INIT_TYPE,**kwargs)
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('graceful',False)
        self.verbose = kwargs.get('verbose',False)
        self.working_dir = WORKING_DIR(self.user)

    def populate_collections(self):

        # Set up environment

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
    
        # Download

        if self.verbose is True:
            print('Downloading company data.')
        company_files = []
        FILE_SUFFIX = '-companylist.csv'
        epoch_time = int(time.time())
        for urlconf in SYMBOL_DATA_URLS:
            target_file = urlconf['exchange']+FILE_SUFFIX
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

        # Clean up received data

        fieldnames = ["Symbol","Name","Last","Capitalization","IPO Year","Sector","Industry","Summary"]
        for company_file in company_files:
            exchange = company_file.rstrip(FILE_SUFFIX)
            if self.verbose is True:
                print('Cleaning up data from exchange "' + exchange + '".')
            repaired_csvfile = open(self.working_dir+company_file+'.import','w+')
            csvfile = open(DOWNLOAD_DIR(self.user)+company_file,'r')
            first_line = csvfile.readline().rstrip(',\n')
            if first_line != FIRST_LINE_STRING:
                self._clean_up(lockfilehandle)
                raise Exception('First line does not match expected format; exiting.')
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
            csvfile = open(self.working_dir+company_file+'.import','r')
            jsonfile = open(self.working_dir+company_file+'.json','w')
            jsonfile.write('[')
            reader = csv.DictReader(csvfile,fieldnames)
            for row in reader:
                for name in fieldnames:
                    if row[name] == 'null':
                        del(row[name])
                row['Exchange'] = exchange
                jsonstring = json.dumps(row)
                jsonfile.write('\n'+jsonstring+',')
            jsonfile.close()
            os.remove(self.working_dir+company_file+'.import')
            with open(self.working_dir+company_file+'.json','rb+') as f:
                f.seek(0,2)
                size=f.tell()
                f.truncate(size-1)
                f.close()
            jsonfile = open(self.working_dir+company_file+'.json','a')
            jsonfile.write('\n]')
            jsonfile.close()
        
        # Create final collection
        
        if self.verbose is True:
            print('Creating unified symbol collection.')
        collection_name = SYMBOL_COLLECTION
        collection = self.db[collection_name]
        collection.drop()
        for urlconf in SYMBOL_DATA_URLS:
            if self.verbose is True:
                print('Importing JSON data for exchange ' + urlconf['exchange']  + '.')
            json_import_file = self.working_dir+urlconf['exchange']+'-companylist.csv.json'
            jsonfile = open(json_import_file,'r')
            json_data = json.loads(jsonfile.read())
            jsonfile.close()
            collection.insert_many(json_data)
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
	
        self._clean_up(lockfilehandle)
	
    def _clean_up(self,lockfilehandle,end_it=True):
        if end_it is True:
            self._record_end()
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

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

class Read(data.Connection):

    def __init__(self,**kwargs):
        super(Read,self).__init__(**kwargs)
        if SYMBOL_COLLECTION not in self.db.list_collection_names():
            raise Exception('Symbol collection "' + SYMBOL_COLLECTION + '" not located in database "' + self.database + '". Collections located: ' + str(self.db.list_collection_names()))
        self.collection = self.db[SYMBOL_COLLECTION]

    def get_symbol(self,symbol,**kwargs):
        symbol = symbol.upper()
        return self.collection.find_one({"Symbol":symbol})
