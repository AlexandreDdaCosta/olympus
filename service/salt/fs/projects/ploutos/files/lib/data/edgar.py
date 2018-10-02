import datetime, fcntl, json, os, re, shutil, sys, time, wget, xmltodict
import edgar as form4_index_downloader

from bson.json_util import dumps, loads

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
                raise Exception('Initialization record check failed; cannot record start of initialization.')

        # The edgar module retrieves based on a starting year. 
        # Check is to see which data sets have already been retrieved and indexed.
        # Then create/update collections as needed.

        # Read existing collections, looking for last worked year, in order oldest to newest
        
        existing_collections = self.db.collection_names()
        start_year = datetime.datetime.now().year
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
            downloaded_entries = []
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
                            downloaded_entries.append(row['cik'] + '_' + row['file'])
                            jsonstring = json.dumps(row)
                            json_data += '\n'+jsonstring+','
                    f.close()
                else:
                    if self.verbose:
                        print(filename + ' not found; skipping.')
            if len(json_data) > 1:
                json_data = json_data[:-1]
            json_data += '\n]'
            downloaded_data = json.loads(json_data)
            if collection_name in existing_collections:
                # Execution check: If number of existing documents match relevant rows
                # in download, assume no changes and skip
                if len(downloaded_entries) == collection.find().count():
                    if self.verbose:
                        print('Download document count matches existing collection; bypassing ' + str(year) + '.')
                    continue
                # Differentiate collections, add missing entries to existing collection
                if self.verbose:
                    print('Differentating new download and existing collection for ' + str(year) + '.')
                existing_entries = []
                for entry in collection.find({}, {'cik':1, 'file':1, '_id':0}):
                    existing_entries.append(entry['cik'] + '_' + entry['file'])
                missing_entries = set(downloaded_entries)-set(existing_entries)
                if len(missing_entries) == 0:
                    if self.verbose:
                        print('No new entries for '+str(year)+'.')
                else:
                    if self.verbose:
                        print('Adding missing entries for '+str(year)+'.')
                    for entry in missing_entries:
                        row = {}
                        row['cik'], row['file'] = entry.split('_')
                        collection.insert_one(row)
            else:
                if self.verbose:
                    print('Loading initial data and creating indices for '+str(year)+'.')
                collection.insert_many(downloaded_data)
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

    INIT_SLEEP = 5
    INIT_WAIT = 20
    #PROCESSING_BLOCK_SIZE = 100
    PROCESSING_BLOCK_SIZE = 5

    def __init__(self,**kwargs):
        super(Form4,self).__init__('form4_submissions',**kwargs)
        self.verbose = kwargs.get('verbose',False)

    def populate_indexed_forms(self,**kwargs):
        # Gather detailed Form4 records based on downloaded EDGAR indices
        self.force = kwargs.get('force',False)
        self.epoch_time = int(time.time())
        year = kwargs.get('year',None)

        if year is not None:
            while True:
                records = self._select_lock_slice(year)
                if len(records) == 0:
                    if self.verbose:
                        print('No unprocessed index entries found for '+str(year)+'; ending.')
                    break
                self._get_write_forms(year,records)
        else:
            for year in QUARTERLY_YEAR_LIST:
                while True:
                    records = self._select_lock_slice(year)
                    if len(records) == 0:
                        if self.verbose:
                            print('No unprocessed index entries found for '+str(year)+'; skipping.')
                        break
                    self._get_write_forms(year,records)

    def _get_write_forms(self,year,records):
        try:
            download_directory = '/tmp/form4_submissions_'+str(os.getpid())+'_'+str(self.epoch_time)+'/'
            if not os.path.isdir(download_directory):
                os.mkdir(download_directory)
            for record in records:
                url = 'https://www.sec.gov/Archives/edgar/data/'+record['cik']+'/'+record['file']+'.txt'
                filename = wget.download(url, out=download_directory+record['cik']+'_'+record['file']+'.txt')
            for record in records:
                filename = download_directory+record['cik']+'_'+record['file']+'.txt'
                xml_content = ''
                xml_found = False
                with open(filename,'r') as f:
                    for line in f:
                        if xml_found is True:
                            if re.match(r'\<\/XML\>',line):
                                break
                            else:
                                xml_content += line
                        elif re.match(r'\<XML\>',line):
                            xml_found = True
                f.close()
                data = xmltodict.parse(xml_content)
                data = data['ownershipDocument']
                cik_owner = data['reportingOwner']['reportingOwnerId']['rptOwnerCik']
                print('\nCIK Owner: '+str(cik_owner))
                foo = bar() # ALEX, intentional error
        except KeyError:
            self._revert_unlock_slice(records,year)
            raise Exception('Key error detected in parsing; check XML format of Form4 submissions for '+str(year))
        except Exception as e:
            self._revert_unlock_slice(records,year)
            raise

    def _revert_unlock_slice(self,records,year):
        collection = self.db[FORM4_INDEX_COLLECTIONS_PREFIX+str(year)]
        bulk = collection.initialize_ordered_bulk_op()
        for record in records:
            bulk.find({ '_id': record['_id'], 'processing': self.epoch_time, 'pid': os.getpid() }).update({ '$unset': { 'processing': 1, 'pid': 1 } })
        bulk.execute()

    def _select_lock_slice(self,year):
        collection = self.db[FORM4_INDEX_COLLECTIONS_PREFIX+str(year)]
        if self.force is True:
            # Unlock all entries being processed
            collection.update({}, {"$unset": {"processing": 1}}, multi=True)

        waits = 0
        while True:
            if self._record_start(year=year) is not True:
                waits = waits + 1
                if waits >= self.INIT_WAIT:
                    if self.verbose:
                        print('Initialization running; exceeded maximum wait time.')
                        return []
                if self.verbose:
                    print('Initialization conflict; waiting '+str(self.INIT_SLEEP)+' seconds.')
                time.sleep(self.INIT_SLEEP)
            else:
                break

        # Go through records where 'cik_owner'/'processing' keys are missing
        # Lock PROCESSING_BLOCK_SIZE entries in main index. 
        
        bulk = collection.initialize_ordered_bulk_op()
        record_count = 0
        records = []
        for record in collection.find({'cik_owner':{'$exists':False},'processing':{'$exists':False}}).limit(self.PROCESSING_BLOCK_SIZE):
            records.append(record)
            bulk.find({ '_id': record['_id'] }).update({ '$set': { 'processing': self.epoch_time, 'pid': os.getpid() } })
        if len(records) > 0:
            bulk.execute()
        self._record_end(year=year)
        return records
