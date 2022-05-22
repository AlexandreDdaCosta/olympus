import time

import olympus.securities.equities.data as data

from olympus import USER

CREDENTIALS_COLLECTION = 'credentials'

class InitCredentials(data.Initializer):

    def __init__(self,username=USER,**kwargs):
        super(InitCredentials,self).__init__(username,CREDENTIALS_COLLECTION,**kwargs)

    def populate_collections(self):
        self.prepare()
        if self.verbose:
            print('Creating credentials collection using a dummy entry.')
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
            self.clean_up()
            raise
        self.clean_up()
