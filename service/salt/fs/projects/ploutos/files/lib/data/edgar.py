import datetime, fcntl, json, re, shutil, sys
import edgar as form4_index_downloader

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

FORM4_INDEX_COLLECTIONS_PREFIX = 'form4_index_'
QUARTERLY_FIRST_YEAR = 2004
QUARTERLY_ORIGINAL_YEAR = 1993
QUARTERLY_YEAR_LIST = range(QUARTERLY_FIRST_YEAR,datetime.datetime.now().year+1)

class InitForm4Indices(data.Connection):

    def __init__(self,**kwargs):
        super(InitForm4Indices,self).__init__('form4_indices',**kwargs)
        self.LOCKFILE = LOCKFILE_DIR+self.init_type+'.pid'
        self.force = kwargs.get('force',False)
        self.graceful = kwargs.get('graceful',False)
        self.verbose = kwargs.get('verbose',False)

    def populate_collections(self):

        # Set up environment

        if self.verbose:
            print('Initializing Form4 collection procedure.')
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
        # Then create/update collections as needed.

        # Read existing collections, looking for last worked year, in order oldest to newest
        
        existing_collections = self.db.collection_names()
        # Subtract one year in case the last created collection was incomplete
        start_year = datetime.datetime.now().year - 1
        for year in QUARTERLY_YEAR_LIST:
            collection_name = FORM4_INDEX_COLLECTIONS_PREFIX+str(year)
            if collection_name not in existing_collections:
                start_year = year - 1
                break
        if start_year < QUARTERLY_FIRST_YEAR:
            start_year = QUARTERLY_FIRST_YEAR
        if self.verbose:
            print('Starting year for init/sync: '+ str(start_year))

		# Download

        if self.verbose:
            print('Downloading quarterly index files.')
        download_directory = '/tmp/form4_indices_'+str(datetime.datetime.utcnow()).replace(" ", "_").replace(":", "_")
        if not os.path.isdir(download_directory):
            os.mkdir(download_directory)
        form4_index_downloader.download_index(download_directory,start_year)

        # Create/update Form 4 index collections, by year

        if self.verbose:
            print('Adding quarterly index files to database.')
        collection_range = range(start_year,datetime.datetime.now().year+1)
        for year in collection_range:
            if self.verbose:
                print('Starting read for '+str(year)+'.')
            collection_name = FORM4_INDEX_COLLECTIONS_PREFIX+str(year)
            collection = self.db[FORM4_INDEX_COLLECTIONS_PREFIX+str(year)]
            if collection_name in existing_collections:
                # Execution check: If number of existing documents match relevant rows
                # in download, assume no changes and skip
                document_count = collection.find().count()
                line_count = 0
                for quarter in (1, 2, 3, 4):
                    filename = download_directory + '/' + str(year) + '-QTR' + str(quarter) + '.tsv'
                    if os.path.isfile(filename):
                        file = open(filename,"r")
                        for line in file:
                            if '|4|' in line or '|4/' in line:
                                line_count = line_count + 1
                        file.close()
                if line_count == document_count:
                    if self.verbose:
                        print('Download document count matches existing collection; bypassing ' + str(year) + '.')
                    continue
                if self.verbose:
                    print('Line count '+ str(line_count) + ', document count ' + str(document_count))
                    print('Collection exists; rebuilding.')
                collection.drop()
            json_data = '['
            for quarter in (1, 2, 3, 4):
                filename = download_directory + '/' + str(year) + '-QTR' + str(quarter) + '.tsv'
                if os.path.isfile(filename):
                    with open(filename) as f:
                        for line in f:
                            pieces = line.rstrip().split('|')
                            if pieces[2] != '4' and pieces[2][:2] != '4/':
                                continue
                            row = {}
                            row['cik'] = pieces[0]
                            row['file'] = pieces[4]
                            row['file'] = re.sub(r'^.*\/(.*)\.txt',r'\g<1>',pieces[4])
                            jsonstring = json.dumps(row)
                            json_data += '\n'+jsonstring+','
                    f.close()
                else:
                    if self.verbose:
                        print(filename + ' not found; skipping.')
            if self.verbose:
                print('Creating indices for '+str(year)+'.')
            if len(json_data) > 1:
                json_data = json_data[:-1]
            json_data += '\n]'
            out_data = json.loads(json_data)
            collection.insert_many(out_data)
            collection.create_index([('cik', pymongo.ASCENDING)], name='cik_'+str(year)+'_'+INDEX_SUFFIX, unique=False)
            collection.create_index([('file', pymongo.ASCENDING)], name='file_'+str(year)+'_'+INDEX_SUFFIX, unique=False)

        # Clean-up
		
        if self.verbose:
            print('Cleaning up.')
        shutil.rmtree(download_directory)
        self._record_end()
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

class Form4(data.Connection):

    def __init__(self,**kwargs):
        super(Form4,self).__init__(**kwargs)
        self.verbose = kwargs.get('verbose',False)
        self.year = kwargs.get('year',None)

    def get_indexed_forms(self):
        # Gather detailed Form4 records based on EDGAR indices
        # Look for an available chunk of the data set to process.
        # Record execution of this chunk
        pass

    def _initialized(self):
        print('foo')
        #
        #Batches of 100 for processing
        #cursor = self.init_collection.find({"datatype":self.init_type})
        #return(Index year, offset)
        return('2004',0) 
