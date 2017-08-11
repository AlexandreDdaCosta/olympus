import csv, datetime, fcntl, json, os, re, socket, wget

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

INIT_TYPE = 'options'
LOCKFILE = LOCKFILE_DIR+'options.pid'
OPTIONS_DATA_URL = 'http://www.cboe.com/publish/scheduledtask/mktdata/cboesymboldir2.csv'

class InitOptions(data.Connection):

    def __init__(self,**kwargs):
        super(InitOptions,self).__init__(**kwargs)
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('force',False)

    def populate_collections(self):
        #LOCKFILE = '/tmp/options.pid' # ALEX
        #DOWNLOAD_DIR = '/tmp/Downloads/' # ALEX
        #WORKING_DIR = '/tmp/' # ALEX

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

        option_file = DOWNLOAD_DIR+'cboesymboldir.csv'
        try:
            os.remove(option_file)
        except OSError:
            pass
        filename = wget.download(OPTIONS_DATA_URL,out=DOWNLOAD_DIR)
        os.rename(filename,option_file)

        # Clean up received data

        fieldnames = ["Name","Symbol","Primary Market","Cycle","Traded on C2","2017","2018","2019","Product Types","Post/Station"]
        
        # Create collections
       
 
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

