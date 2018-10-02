import ast, csv, datetime, fcntl, json, os, re, socket, wget

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

INIT_TYPE = 'options'
LOCKFILE = LOCKFILE_DIR+INIT_TYPE+'.pid'
OPTIONS_COLLECTIONS_PREFIX = 'options_'
OPTIONS_DATA_URL = 'http://www.cboe.com/publish/scheduledtask/mktdata/cboesymboldir2.csv'
WORKING_FILE = 'cboesymboldir.csv'

FIRST_ROW_STRING = "{'2018': None, '2019': None, '2020': None, 'Post/Station': None, 'Product Types': None, 'Cycle': None, 'Primary Market': None, 'Name': 'NOTE: All directories are updated daily using information from the previous business day.', 'Traded on C2': None, 'Symbol': None}"
SECOND_ROW_STRING = "{'2018': 'LEAPS 2019', '2019': 'LEAPS 2020', '2020': 'LEAPS 2021', 'Post/Station': ' Post/Station', 'Product Types': 'Product Types', 'Cycle': 'Cycle', 'Primary Market': 'DPM', 'Name': 'Company Name', 'Traded on C2': 'Traded at C2', 'Symbol': 'Stock Symbol'}"

class InitOptions(data.Connection):

    def __init__(self,**kwargs):
        super(InitOptions,self).__init__(INIT_TYPE,**kwargs)
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('force',False)

    def populate_collections(self):

        # Set up environment

        lockfilehandle = open(LOCKFILE,'w')
        fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lockfilehandle.write(str(os.getpid()))
        os.chdir(WORKING_DIR)
       
        if self._record_start() is not True:
            if self.graceful is True:
                lockfilehandle.write('')
                fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
                lockfilehandle.close()
                return
            else:
                raise Exception('Data initialization detected; exiting.')
        host, pid = self._initialized()
        if host != socket.gethostname() or pid != os.getpid():
            raise Exception('Initialization record check failed; cannot record start of initialization.')
    
		# Download

        option_file = DOWNLOAD_DIR+WORKING_FILE
        try:
            os.remove(option_file)
        except OSError:
            pass
        filename = wget.download(OPTIONS_DATA_URL,out=DOWNLOAD_DIR)
        os.rename(filename,option_file)

        # Clean up received data

        fieldnames = ["Name","Symbol","Primary Market","Cycle","Traded on C2","2018","2019","2020","Product Types","Post/Station"]
        csvfile = open(DOWNLOAD_DIR+WORKING_FILE,'r')
        jsonfile = open(WORKING_DIR+WORKING_FILE+'.json','w')
        jsonfile.write('[')
        reader = csv.DictReader(csvfile,fieldnames)
        rowcount = 0
        for row in reader:
            # The rowcounts are for a pseudo-verification of file format
            rowcount = rowcount + 1
            if rowcount == 1:
                if row != ast.literal_eval(FIRST_ROW_STRING.strip('\n')):
                    raise Exception('First row does not match expected format; exiting. \n['+str(row)+']\n['+FIRST_ROW_STRING+']')
            elif rowcount == 2:
                if row != ast.literal_eval(SECOND_ROW_STRING.strip('\n')):
                    raise Exception('Second row does not match expected format; exiting. \n['+str(row)+']\n['+SECOND_ROW_STRING+']')
            else:
                for name in fieldnames:
                    if row[name] == '' or row[name] is None:
                        del(row[name])
                jsonstring = json.dumps(row)
                jsonfile.write('\n'+jsonstring+',')
        jsonfile.close()
        with open(WORKING_DIR+WORKING_FILE+'.json','rb+') as f:
            f.seek(0,2)
            size=f.tell()
            f.truncate(size-1)
            f.seek(0,2)
            f.write(bytes('\n]','UTF-8'))
            f.close()
        
        # Create collection
       
        json_import_file = WORKING_DIR+WORKING_FILE+'.json'
        option_file = DOWNLOAD_DIR+WORKING_FILE
        collection = self.db[OPTIONS_COLLECTIONS_PREFIX+'cboe']
        collection.drop()
        jsonfile = open(json_import_file,'r')
        json_data = json.loads(jsonfile.read())
        jsonfile.close()
        collection.insert_many(json_data)
        collection.create_index("Symbol")
		
        # Clean-up
		
        self._record_end()
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()
