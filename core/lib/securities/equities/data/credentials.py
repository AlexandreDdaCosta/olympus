import fcntl, os, time

import olympus.securities.equities.data as data

from olympus import USER, DOWNLOAD_DIR, LOCKFILE_DIR, WORKING_DIR

INIT_TYPE = 'credentials'
CREDENTIALS_COLLECTION = 'credentials'

class InitCredentials(data.Connection):

    def __init__(self,user=USER,**kwargs):
        super(InitCredentials,self).__init__(user,INIT_TYPE,**kwargs)
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
      
        if self._record_start() is not True:
            self._clean_up(lockfilehandle,False)
            if self.graceful is True:
                print('Initialization record check failed; cannot record start of initialization.')
                return
            else:
                raise Exception('Initialization record check failed; cannot record start of initialization.')
    
        # Create collection using a dummy entry
       
        collection = self.db[CREDENTIALS_COLLECTION]
        dummy_record = {'DataSource': 'DUMMY', 'KeyName': 'dummy_name', 'Key': 'dummy_key', 'IssueEpochDate': int(time.time())}
        collection.replace_one({'DataSource': 'DUMMY'}, dummy_record, upsert=True)
        if self.verbose is True:
            print('Indexing collection.')
        try:
            if self.verbose is True:
                print('Indexing "DataSource".')
            collection.create_index("DataSource")
        except:
            self._clean_up(lockfilehandle)
            raise
		
        self._clean_up(lockfilehandle)
	
    def _clean_up(self,lockfilehandle,end_it=True):
        if end_it is True:
            self._record_end()
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

