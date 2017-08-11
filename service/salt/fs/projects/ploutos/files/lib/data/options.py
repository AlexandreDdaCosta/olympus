import csv, datetime, fcntl, json, os, re, socket, wget

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

INIT_TYPE = 'options'
LOCKFILE = LOCKFILE_DIR+INIT_TYPE+'.pid'
OPTIONS_DATA_URL = 'http://www.cboe.com/publish/scheduledtask/mktdata/cboesymboldir2.csv'
WORKING_FILE_NAME = 'cboesymboldir.csv'

class InitOptions(data.Connection):

    def __init__(self,**kwargs):
        super(InitOptions,self).__init__(**kwargs)
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('force',False)

    def populate_collections(self):
        LOCKFILE = '/tmp/options.pid' # ALEX
        DOWNLOAD_DIR = '/tmp/Downloads/' # ALEX
        WORKING_DIR = '/tmp/' # ALEX

        # Set up environment
        lockfilehandle = open(LOCKFILE,'w')
        fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lockfilehandle.write(str(os.getpid()))
        os.chdir(WORKING_DIR)
       
        if self._record_start(INIT_TYPE) is not True:
            if self.graceful is True:
                lockfilehandle.write('')
                fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
                lockfilehandle.close()
                return
            else:
                raise Exception('Data initialization detected; exiting.')
        if self._initialized(INIT_TYPE) != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record start of initialization.')
    
		# Download

        option_file = DOWNLOAD_DIR+WORKING_FILE_NAME
        try:
            os.remove(option_file)
        except OSError:
            pass
        filename = wget.download(OPTIONS_DATA_URL,out=DOWNLOAD_DIR)
        os.rename(filename,option_file)

        # Clean up received data

        fieldnames = ["Name","Symbol","Primary Market","Cycle","Traded on C2","2017","2018","2019","Product Types","Post/Station"]
        csvfile = open(DOWNLOAD_DIR+WORKING_FILE_NAME,'r')
        jsonfile = open(WORKING_DIR+WORKING_FILE_NAME+'.json','w')
        jsonfile.write('[')
        reader = csv.DictReader(csvfile,fieldnames)
        rowcount = 0
        for row in reader:
            # The rowcounts are a pseudo-verification of file format
            rowcount = rowcount + 1
            if rowcount == 1:
                print(row)
            elif rowcount == 1:
                print(row)
            else:
                for name in fieldnames:
                    if row[name] == '' or row[name] is null:
                        del(row[name])
                jsonstring = json.dumps(row)
                jsonfile.write('\n'+jsonstring+',')
        jsonfile.close()
        with open(WORKING_DIR+WORKING_FILE+'.json','rb+') as f:
            f.seek(0,2)
            size=f.tell()
            f.truncate(size-1)
            f.seek(0,0)
            f.write('\n]')
            f.close()
        
        # Create collection
       
        json_import_file = WORKING_DIR+WORKING_FILE_NAME+'.json'
        option_file = DOWNLOAD_DIR+WORKING_FILE_NAME
        collection = self.db[OPTIONS_COLLECTION]
        collection.drop()
        jsonfile = open(json_import_file,'r')
        json_data = json.loads(jsonfile.read())
        jsonfile.close()
        collection.insert_many(json_data)
		
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()
