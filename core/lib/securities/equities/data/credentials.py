import fcntl, os, time

import olympus.securities.equities.data as data

from olympus import USER, User

DATA_TYPE = 'credentials'
CREDENTIALS_COLLECTION = DATA_TYPE

class InitCredentials(data.Connection):

    def __init__(self,user=USER,**kwargs):
        super(InitCredentials,self).__init__(user,DATA_TYPE,**kwargs)
        self.verbose = kwargs.get('verbose',False)
        self.user_object = User(user)
        self.working_dir = self.user_object.working_directory()
        self.lockfile = self.user_object.lockfile_directory()+DATA_TYPE+'.pid'

    def populate_collections(self):

        # Set up environment

        lockfilehandle = open(self.lockfile,'w')
        fcntl.flock(lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        lockfilehandle.write(str(os.getpid()))
        os.chdir(self.working_dir)
      
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
	
    def _clean_up(self,lockfilehandle):
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()
