import fnctl, os

import olympus.mongodb as mongodb

from olympus import USER, User

DATABASE = 'equities'
INDEX_SUFFIX = '_idx'
URLS = {
   "ALPHAVANTAGE": "https://www.alphavantage.co/query?apikey=",
   "YAHOO_FINANCE": "https://query1.finance.yahoo.com/v7/finance/download/",
   "TD_AMERITRADE": "https://api.tdameritrade.com/v1/"
}

# Collections

class Connection(mongodb.Connection):

    def __init__(self,username=USER,**kwargs):
        super(Connection,self).__init__(username)
        self.verbose = kwargs.get('verbose',False)
        self.database = DATABASE
        if self.verbose:
            print('Establishing MongoDB client to database ' + self.database + '.')
        self.connect(self.database)

class Initializer(Connection):

    def __init__(self,username=USER,data_type,**kwargs):
        super(Initializer,self).__init__(username,**kwargs)
        self.user_object = User(self.username)
        self.download_directory = self.user_object.download_directory()
        self.working_directory = self.user_object.working_directory()
        self.lockfile = self.user_object.lockfile_directory()+data_type+'.pid'
        self.data_type = data_type
        try:
            os.makedirs(self.download_directory)
        except OSError:
            pass

    def clean_up(self):
        if self.verbose:
            print('Cleaning up data population process for '+self.data_type+'.')
        if self.lockfilehandle is not None:
            self.lockfilehandle.write('')
            fcntl.flock(self.lockfilehandle,fcntl.LOCK_UN)
            self.lockfilehandle.close()

    def prepare(self):
        if self.verbose:
            print('Setting up data population for '+self.data_type+'.')
        self.lockfilehandle = open(self.lockfile,'w')
        fcntl.flock(self.lockfilehandle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.lockfilehandle.write(str(os.getpid()))
        os.chdir(self.working_directory)
