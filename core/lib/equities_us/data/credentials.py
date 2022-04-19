import fcntl, os

import olympus.equities_us.data as data

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
    
        # Create collection
       
        collection = self.db[CREDENTIALS_COLLECTION]
		
        self._clean_up(lockfilehandle)
	
    def _clean_up(self,lockfilehandle,end_it=True):
        if end_it is True:
            self._record_end()
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

