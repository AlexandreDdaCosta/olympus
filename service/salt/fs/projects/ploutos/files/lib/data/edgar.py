import datetime, fcntl, json, re
import edgar as form4_index_downloader

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

FORM4_INDEX_COLLECTIONS_PREFIX = 'form4_index_'
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

        # The edgar module retrieves based on a starting year. 
        # Check is to see which data sets have already been retrieved and indexed.

        # Index/create collection
        existing_collections = self.db.collection_names()
        start_year = datetime.datetime.now().year+1
        for year in QUARTERLY_YEAR_LIST:
            collection_name = FORM4_INDEX_COLLECTIONS_PREFIX+str(year)
            if collection_name not in existing_collections:
                start_year = year
                break

        # ?. Read completion entries (start with last incomplete quarter, if any)

		# Download

        download_directory = '/tmp/form4_indices_2018-09-25_03_20_48.208421/'
        #download_directory = '/tmp/form4_indices_'+str(datetime.datetime.utcnow()).replace(" ", "_").replace(":", "_")
        #if not os.path.isdir(download_directory):
        #    os.mkdir(download_directory)
        #form4_index_downloader.download_index(download_directory,start_year)

        # Create and populate Form 4 index collections, by year

        collection_range = range(start_year,datetime.datetime.now().year+1)
        for year in collection_range:
            json_data = '['
            for quarter in (1, 2, 3, 4):
                filename = download_directory + str(year) + '-QTR' + str(quarter) + '.tsv'
                if os.path.isfile(filename):
                    with open(filename) as f:
                        for line in f:
                            pieces = line.rstrip().split('|')
                            if pieces[2][:1] != '4':
                                continue
                            row = {}
                            row['cik'] = pieces[0]
                            row['file'] = pieces[4]
                            # "edgar/data/1000015/0001047469-04-001808.txt"
                            row['file'] = re.sub(r'^.*\/(.*)\.txt',r'\g<1>',pieces[4])
                            jsonstring = json.dumps(row)
                            json_data += '\n'+jsonstring+','
            if len(json_data) > 1:
                json_data = json_data[:-1]
            json_data += '\n]'
            out_data = json.loads(json_data)
            collection_name = FORM4_INDEX_COLLECTIONS_PREFIX+str(year)
            collection = self.db[FORM4_INDEX_COLLECTIONS_PREFIX+str(year)]
            collection.insert_many(out_data)
            #collection.create_index("Symbol")
            #collection.create_index([('quarter', pymongo.ASCENDING)], name='quarter'+FORM4_INDEX_SUFFIX, unique=False)
            raise Exception('ALEX')
		
        # Unlock process
		
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()
