import edgar, fcntl

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

class InitQuarterlyIndices(data.Connection):

    def __init__(self,**kwargs):
        super(InitQuarterlyIndices,self).__init__(**kwargs)
        self.INIT_TYPE = 'edgar_indices'
        self.LOCKFILE = LOCKFILE_DIR+INIT_TYPE+'.pid'
        self.FIRST_YEAR = '1993'
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('force',False)

    def populate_collections(self):

        # Set up environment

        lockfilehandle = open(self.LOCKFILE,'w')
        fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lockfilehandle.write(str(os.getpid()))
        os.chdir(WORKING_DIR)
       
        if self._record_start(self.INIT_TYPE) is not True:
            if self.graceful is True:
                lockfilehandle.write('')
                fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
                lockfilehandle.close()
                return
            else:
                raise Exception('Data initialization detected; exiting.')
        if self._initialized(self.INIT_TYPE) != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record start of initialization.')
    
		# Check for existing completed indices
        # ?. Read completion entries (start with last incomplete quarter, if any)

		# Download

        #edgar.download_index(download_directory, since_year)
        edgar.download_index(DOWNLOAD_DIR,'2017')

        # Clean up received data

        
        # Create collection
		
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()
