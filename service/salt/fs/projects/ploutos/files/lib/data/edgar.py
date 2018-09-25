import datetime, fcntl
import edgar as form4_index_downloader

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

FORM4_INDEX_COLLECTIONS_PREFIX = 'form4_'
FORM4_INDEX_SUFFIX = '_form4' + INDEX_SUFFIX
QUARTERLY_FIRST_YEAR = 2004
QUARTERLY_ORIGINAL_YEAR = 1993
QUARTERLY_YEAR_LIST = range(QUARTERLY_FIRST_YEAR,datetime.datetime.now().year+1)

class InitForm4Indices(data.Connection):

    def __init__(self,**kwargs):
        super(InitForm4Indices,self).__init__('form4_indices',**kwargs)
        self.LOCKFILE = LOCKFILE_DIR+self.init_type+'.pid'
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
                raise Exception('Initialization of EDGAR Form4 indices detected; exiting.')
        if self._initialized() != socket.gethostname():
            raise Exception('Initialization record check failed; cannot record start of initialization.')

		# Check for existing completed years/quarters
        # The edgar module retrieves based on a starting date. Our check is to see 
        # which data sets have already been retrieved and indexed.

        # Index/create collection
        existing_collections = self.db.collection_names()
        start_year = datetime.datetime.now().year+1
        for year in QUARTERLY_YEAR_LIST:
            collection_name = FORM4_INDEX_COLLECTIONS_PREFIX+'quarterlies_'+str(year)
            if collection_name not in existing_collections:
                start_year = year
                break

        # ?. Read completion entries (start with last incomplete quarter, if any)

		# Download

        #download_directory = '/tmp/form4_indices_'+str(datetime.datetime.utcnow()).replace(" ", "_").replace(":", "_")
        #if not os.path.isdir(download_directory):
        #    os.mkdir(download_directory)
        #form4_index_downloader.download_index(download_directory,start_year)

        # Clean up received data

        
        # Create collection
		
        #collection.create_index([('quarter', pymongo.ASCENDING)], name='quarter'+FORM4_INDEX_SUFFIX, unique=False)
		
        # Unlock process
		
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()
