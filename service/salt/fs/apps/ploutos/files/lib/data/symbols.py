import ast, csv, datetime, fcntl, json, os, re, socket, wget

import olympus.apps.ploutos.data as data

from olympus.apps.ploutos import *
from olympus.apps.ploutos.data import *

INIT_TYPE = 'symbols'
LOCKFILE = LOCKFILE_DIR+INIT_TYPE+'.pid'
NORMALIZE_CAP_REGEX = re.compile('[^0-9\.]')
SYMBOL_COLLECTIONS_PREFIX = 'symbols_'
SYMBOL_DATA_URLS = [
{'exchange':'amex','url':'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=amex&render=download'},
{'exchange':'nasdaq','url':'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download'},
{'exchange':'nyse','url':'http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download'}
]

FIRST_LINE_STRING = '"Symbol","Name","LastSale","MarketCap","IPOyear","Sector","industry","Summary Quote"'

class InitSymbols(data.Connection):

    def __init__(self,**kwargs):
        super(InitSymbols,self).__init__(INIT_TYPE,**kwargs)
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('graceful',False)

    def populate_collections(self):

        # Set up environment

        lockfilehandle = open(LOCKFILE,'w')
        fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lockfilehandle.write(str(os.getpid()))
        os.chdir(WORKING_DIR)
       
        if self._record_start() is not True:
            self._clean_up(lockfilehandle,False)
            if self.graceful is True:
                print('Initialization record check failed; cannot record start of initialization.')
                return
            else:
                raise Exception('Initialization record check failed; cannot record start of initialization.')
    
        # Download

        company_files = []
        for urlconf in SYMBOL_DATA_URLS:
            target_file = urlconf['exchange']+'-companylist.csv'
            company_files.insert(0,target_file)
            target_file = DOWNLOAD_DIR+target_file
            try:
                os.remove(target_file)
            except OSError:
                pass
            try:
                filename = wget.download(urlconf['url'],out=DOWNLOAD_DIR)
            except Exception as e:
                self._clean_up(lockfilehandle)
                if self.graceful is True:
                    print('WARNING: Bypassing initialization due to download error: '+str(e))
                    return
                raise
            os.rename(filename,target_file)

        # Clean up received data

        fieldnames = ["Symbol","Name","Last","Capitalization","IPO Year","Sector","Industry","Summary"]
        for company_file in company_files:
            repaired_csvfile = open(WORKING_DIR+company_file+'.import','w+')
            csvfile = open(DOWNLOAD_DIR+company_file,'r')
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
            csvfile = open(WORKING_DIR+company_file+'.import','r')
            jsonfile = open(WORKING_DIR+company_file+'.json','w')
            jsonfile.write('[')
            reader = csv.DictReader(csvfile,fieldnames)
            for row in reader:
                for name in fieldnames:
                    if row[name] == 'null':
                        del(row[name])
                jsonstring = json.dumps(row)
                jsonfile.write('\n'+jsonstring+',')
            jsonfile.close()
            os.remove(WORKING_DIR+company_file+'.import')
            with open(WORKING_DIR+company_file+'.json','rb+') as f:
                f.seek(0,2)
                size=f.tell()
                f.truncate(size-1)
                f.close()
            jsonfile = open(WORKING_DIR+company_file+'.json','a')
            jsonfile.write('\n]')
            jsonfile.close()
        
        # Create collections
        
        for urlconf in SYMBOL_DATA_URLS:
            json_import_file = WORKING_DIR+urlconf['exchange']+'-companylist.csv.json'
            collection_name = SYMBOL_COLLECTIONS_PREFIX + urlconf['exchange']
            collection = self.db[collection_name]
            collection.drop()
            jsonfile = open(json_import_file,'r')
            json_data = json.loads(jsonfile.read())
            jsonfile.close()
            collection.insert_many(json_data)
            collection.create_index("Symbol")
	
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