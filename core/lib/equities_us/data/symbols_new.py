import ast, csv, datetime, fcntl, json, os, re, socket, subprocess, time

import olympus.equities_us.data as data

from olympus import USER, DOWNLOAD_DIR, LOCKFILE_DIR, WORKING_DIR

INIT_TYPE = 'symbols'
SYMBOL_COLLECTION = INIT_TYPE
SYMBOL_DATA_URLS = [
{'url':'ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt','first_line_string':'Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares'},
{'url':'ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt','first_line_string':'ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol'}
]

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
            target_file = urlconf['url'].rsplit('/', 1)[-1]
            company_files.insert(0,target_file)
            target_file_local = DOWNLOAD_DIR(self.user)+target_file
            if self.force is False:
                # Download site issues; use existing downloads if not too old
                if os.path.isfile(target_file_local) and os.stat(target_file_local).st_size > 1:
                    if epoch_time - os.stat(target_file_local).st_mtime < 28800:
                        print('Using existing company list for ' + target_file + ': Less than eight hours old.')
                        continue
            if self.verbose is True:
                print('Downloading company data, URL ' + urlconf['url'])
            try:
                os.remove(target_file)
            except OSError:
                pass
            try:
                # None of the python options works, even when specifying user-agent
                subprocess.run(['wget "'+urlconf['url']+'" --timeout=10 --user-agent=' + self.user + ' --output-document='+target_file_local], shell=True)
            except Exception as e:
                self._clean_up(lockfilehandle)
                if self.graceful is True:
                    print('WARNING: Bypassing initialization due to download error: '+str(e))
                    return
                raise

        for company_file in company_files:
            if self.verbose is True:
                print('Evaluating downloaded file ' + company_file)


        # ALEX
        self._clean_up(lockfilehandle)
	
    def _clean_up(self,lockfilehandle,end_it=True):
        if self.verbose is True:
            print('Cleaning up environment.')
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
