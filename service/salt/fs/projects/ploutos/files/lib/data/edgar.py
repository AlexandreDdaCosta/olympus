import edgar, fcntl

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

class InitQuarterlyIndices(data.Connection):

    def __init__(self,**kwargs):
        super(InitQuarterlyIndices,self).__init__('edgar_indices',**kwargs)
        self.LOCKFILE = LOCKFILE_DIR+self.init_type+'.pid'
        self.FIRST_YEAR = '1993'
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('force',False)

    def populate_collections(self):

        # Set up environment

        lockfilehandle = open(self.LOCKFILE,'w')
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
                raise Exception('Initialization of edgar indices detected; exiting.')
        if self._initialized() != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record start of initialization.')

		# Check for existing completed indices
        # The edgar module retrieves based on a starting date. Our check is to see 
        # which data sets have already been retrieved and indexed.

        # ?. Read completion entries (start with last incomplete quarter, if any)

		# Download

        #edgar.download_index(download_directory, since_year)
        #edgar.download_index(DOWNLOAD_DIR,'2017')

        # Clean up received data

        
        # Create collection
		
        # Unlock process
		
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()
