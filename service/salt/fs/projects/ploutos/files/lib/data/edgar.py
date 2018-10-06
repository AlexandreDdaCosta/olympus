import datetime, fcntl, json, os, re, shutil, sys, time, wget, xmlschema, xmltodict
import edgar as form4_index_downloader

from bson.json_util import dumps, loads

import olympus.projects.ploutos.data as data

from olympus.projects.ploutos import *
from olympus.projects.ploutos.data import *

FORM4_INDEX_COLLECTION_NAME = 'form4_indices'
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
        # Read existing collection, looking for last worked year, in order oldest to newest
        
        collection = self.db[FORM4_INDEX_COLLECTION_NAME]
        existing_collections = self.db.collection_names()
        create_indices = False
        if FORM4_INDEX_COLLECTION_NAME not in existing_collections:
            start_year = QUARTERLY_FIRST_YEAR
            create_indices = True
        else:
            start_year = datetime.datetime.now().year
            for year in QUARTERLY_YEAR_LIST:
                if collection.find({'year': year}).count() == 0:
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

        # Create/update Form 4 index collections, in year order

        if self.verbose:
            print('Adding quarterly index files to database.')
        collection_range = range(start_year,datetime.datetime.now().year+1)
        for year in collection_range:
            if self.verbose:
                print('Starting read for '+str(year)+'.')
            downloaded_entries = []
            json_data = '['
            for quarter in (1, 2, 3, 4):
                filename = download_directory + '/' + str(year) + '-QTR' + str(quarter) + '.tsv'
                if os.path.isfile(filename):
                    with open(filename) as f:
                        for line in f:
                            pieces = line.rstrip().split('|')
                            if pieces[2] != '4' and pieces[2][:3] != '4/A':
                                continue
                            row = {}
                            row['issuerCik'] = int(pieces[0])
                            row['file'] = pieces[4]
                            row['file'] = re.sub(r'^.*\/(.*)\.txt',r'\g<1>',pieces[4])
                            row['form'] = str(pieces[2])
                            row['year'] = year
                            downloaded_entries.append(str(row['issuerCik']) + '_' + row['file'] + '_' + row['form'])
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

            year_document_count = collection.find({'year': year}).count()
            if year_document_count > 0:
                # Execution check: If number of existing documents match relevant rows
                # in download, assume no changes and skip
                if len(downloaded_entries) == year_document_count:
                    if self.verbose:
                        print('Download document count matches count of existing documents; bypassing ' + str(year) + '.')
                    continue
                # Differentiate collections, add missing entries to existing collection
                if self.verbose:
                    print('Differentating new download and existing collection for ' + str(year) + '.')
                existing_entries = []
                for entry in collection.find({'year': year}, {'issuerCik':1, 'file':1, 'form':1, '_id':0}):
                    existing_entries.append(str(entry['issuerCik']) + '_' + entry['file'] + '_' + entry['form'])
                missing_entries = set(downloaded_entries)-set(existing_entries)
                if len(missing_entries) == 0:
                    if self.verbose:
                        print('No new entries for '+str(year)+'.')
                else:
                    if self.verbose:
                        print('Adding missing entries for '+str(year)+'.')
                    for entry in missing_entries:
                        row = {}
                        row['issuerCik'], row['file'], row['form'] = entry.split('_')
                        row['issuerCik'] = int(row['issuerCik'])
                        row['form'] = str(row['form'])
                        row['year'] = year
                        collection.insert_one(row)
            else:
                if self.verbose:
                    print('Loading initial data for '+str(year)+'.')
                collection.insert_many(downloaded_data)

            if create_indices is True:
                if self.verbose:
                    print('Creating indices for ' + FORM4_INDEX_COLLECTION_NAME)
                collection.create_index([('issuerCik', pymongo.ASCENDING)], name=FORM4_INDEX_COLLECTION_NAME+'_issuerCik_'+INDEX_SUFFIX, unique=False)
                collection.create_index([('file', pymongo.ASCENDING)], name=FORM4_INDEX_COLLECTION_NAME+'_file_'+INDEX_SUFFIX, unique=False)
                collection.create_index([('year', pymongo.ASCENDING)], name=FORM4_INDEX_COLLECTION_NAME+'_year_'+INDEX_SUFFIX, unique=False)
                create_indices = False

        # Clean-up
		
        if self.verbose:
            print('Cleaning up.')
        shutil.rmtree(download_directory)
        self._record_end()
        lockfilehandle.write('')
        fcntl.flock(lockfilehandle,fcntl.LOCK_UN)
        lockfilehandle.close()

class Form4(data.Connection):

    FORM4_SUBMISSIONS_COLLECTION_NAME = 'form4_submissions'
    ISSUER_COLLECTION_NAME = 'issuer'
    REPORTING_OWNER_COLLECTION_NAME = 'reporting_owner'
    INIT_SLEEP = 5
    INIT_WAIT = 20
    PROCESSING_BLOCK_SIZE = 100

    def __init__(self,**kwargs):
        super(Form4,self).__init__('form4_submissions',**kwargs)
        self.verbose = kwargs.get('verbose',False)

    def populate_indexed_forms(self,**kwargs):
        # Gather detailed Form4 records based on downloaded EDGAR indices
        self.force = kwargs.get('force',False)
        self.epoch_time = int(time.time())
        schema_directory = re.sub(r'(.*\/).*?$',r'\1', os.path.dirname(os.path.realpath(__file__)) ) + 'schema/'
        self.form4_schema = xmlschema.XMLSchema(schema_directory + 'ownership4Document.xsd.xml')
        self.form4a_schema = xmlschema.XMLSchema(schema_directory + 'ownership4ADocument.xsd.xml')

        cik_file = kwargs.get('cik_file',None)
        self.max_records = kwargs.get('max_records',0)
        self.max_record_count = 0
        year = kwargs.get('year',None)
        self.collection_index = self.db[FORM4_INDEX_COLLECTION_NAME]
        self.collection_issuer = self.db[self.ISSUER_COLLECTION_NAME]
        self.collection_issuer.create_index([('issuerCik', pymongo.ASCENDING)], name=self.ISSUER_COLLECTION_NAME+'_issuerCik_'+INDEX_SUFFIX, unique=True)
        self.collection_reporting_owner = self.db[self.REPORTING_OWNER_COLLECTION_NAME]
        self.collection_reporting_owner.create_index([('rptOwnerCik', pymongo.ASCENDING)], name=self.REPORTING_OWNER_COLLECTION_NAME+'_rptOwnerCik_'+INDEX_SUFFIX, unique=True)
        self.collection_submissions = self.db[self.FORM4_SUBMISSIONS_COLLECTION_NAME]
        self.collection_submissions.create_index([('rptOwnerCik', pymongo.ASCENDING)], name=self.FORM4_SUBMISSIONS_COLLECTION_NAME+'_rptOwnerCik_'+INDEX_SUFFIX, unique=True)

        if cik_file is not None:
            if self.verbose:
                print('Running single Form4 update for '+ cik_file)
            issuerCik, filename = re.split(r'-', cik_file)
            records = []
            for record in self.collection_submissions.find({'issuerCik': int(issuerCik),'processing':{'$exists':False},'year':int(year)}):
                records.append(record)
            if len(records) == 0:
                raise Exception('Specified cik/file combination not found in indices: ' + cik_file)
            elif len(records) > 1:
                raise Exception('Specified cik/file combination found ' + str(len(records)) + ' times in indices: ' + cik_file)
            self._get_write_forms(year,records)
        elif year is not None:
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

    def _convert_period_of_report(self, submission_date):
        year, month, day = str(submission_date).split('-')
        t = datetime.datetime(year, month, day, 0, 0)
        return time.mktime(t.timetuple())

    def _get_write_forms(self,year,records):
        download_directory = '/tmp/form4_submissions_'+str(os.getpid())+'_'+str(self.epoch_time)+'/'
        try:
            if not os.path.isdir(download_directory):
                os.mkdir(download_directory)
            for record in records:
                url = 'https://www.sec.gov/Archives/edgar/data/'+str(record['issuerCik'])+'/'+record['file']+'.txt'
                filename = wget.download(url, out=download_directory+str(record['issuerCik'])+'_'+record['file']+'.txt')
                if self.verbose:
                    print('\n')
               filename = download_directory+str(record['issuerCik'])+'_'+record['file']+'.txt'
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
                #xml_content = xml_content.replace("\n", "")
                data = {}
                try:
                    if record['form'] == '4/A':
                        xmlschema.validate(xml_content,schema=self.form4a_schema)
                    else:
                        xmlschema.validate(xml_content,schema=self.form4_schema)
                    data = xmltodict.parse(xml_content)
                except Exception as e:
                    if self.verbose:
                        print(json.dumps(data,indent=4))
                        print('\n\nhttps://www.sec.gov/Archives/edgar/data/'+str(record['issuerCik'])+'/'+record['file']+'.txt\n')
                    self._revert_unlock_slice(records)
                    raise

                # issuerCik document
                if self.collection_issuer.find({'issuerCik': record['issuerCik']}).limit(1).count() == 0:
                    self.collection_issuer.update({'issuerCik': record['issuerCik']},{'issuerCik': record['issuerCik']}, upsert=True)
                    self.collection_issuer.update({'issuerCik': record['issuerCik']}, {'$set': {'issuer': {}, 'history': {}}})
                submission_date = self._convert_period_of_report(data['ownershipDocument']['periodOfReport'])
                issuer_record = {}
                for issuer_record in self.collection_issuer.find({'issuerCik': record['issuerCik']}):
                    break
                new_dict = {}
                new_dict['periodOfReport'] = submission_date
                new_dict['issuerName'] = data['ownershipDocument']['issuer']['issuerName'].upper()
                new_dict['issuerTradingSymbol'] = data['ownershipDocument']['issuer']['issuerTradingSymbol'].upper()
                if len(issuer_record['issuer']) == 0: 
                    self.collection_issuer.update({'_id': issuer_record['_id']}, {'$set': {'issuer': new_dict}})
                elif issuer_record['issuer']['periodOfReport'] < submission_date:
                    if issuer_record['issuer']['issuerName'] != new_dict['issuerName'] or
                            issuer_record['issuer']['issuerTradingSymbol'] != new_dict['issuerTradingSymbol']:
                        historic_dict = {}
                        historic_dict['issuerName'] = issuer_record['issuer']['issuerName']
                        historic_dict['issuerTradingSymbol'] = issuer_record['issuer']['issuerTradingSymbol']
                        self.collection_issuer.update({'_id': issuer_record['_id']}, {'$set': {'issuer': new_dict, 'history.'+issuer_record['issuer']['periodOfReport']: historic_dict }})

                # reportingOwner document + submission data
                owner_cik = []
                if type(data['ownershipDocument']['reportingOwner']) is list:
                    rptOwnerCik = int(data['ownershipDocument']['reportingOwner']['reportingOwnerId']['rptOwnerCik'])
                    owner_cik.append(rptOwnerCik)
                else:
                    rptOwnerCik = self._reporting_owner_handler(data,record)
                    owner_cik.append(rptOwnerCik)
                # Form4 index
                self.collection_index.update({'issuerCik':record['issuerCik'], 'file':record['file']}, {'$set': { 'rptOwnerCik': owner_cik }, '$unset': { 'processing': 1, 'pid': 1 }} )
                if self.verbose:
                    print('UPDATED INDEX: '+ str(record['issuerCik']) + ' ' + str(record['file']))

        except KeyError:
            self._revert_unlock_slice(records)
            raise Exception('Key error detected in parsing; check XML format of Form4 submissions for '+str(year))
        except Exception as e:
            self._revert_unlock_slice(records)
            raise

    def _reporting_owner_handler(self,data,record):
        rptOwnerCik = int(data['ownershipDocument']['reportingOwner']['reportingOwnerId']['rptOwnerCik'])
        self.collection_submissions.update({'rptOwnerCik':rptOwnerCik},{'rptOwnerCik':rptOwnerCik}, upsert=True)
        if self.verbose:
            print('VERIFIED CIK OWNER: '+ str(rptOwnerCik))

        # Core data structure for new submission
        if self.collection_submissions.find({'rptOwnerCik':rptOwnerCik, 'issuerCik': {'$exists': True}}).limit(1).count() == 0:
            self.collection_submissions.update({'rptOwnerCik':rptOwnerCik}, {'$set': {'issuerCik': {}}})
        self.collection_submissions.update({'rptOwnerCik':rptOwnerCik}, {'$set': {'issuerCik.'+str(record['issuerCik'])+'.'+record['file']: { 'reportingOwner': {}, 'nonDerivativeTransaction': [], 'derivativeTransaction': [] }}})

        # Populate submission data structures
        # ALEX TBC

        # Add/update reporting owner data
        if self.collection_reporting_owner.find({'rptOwnerCik': rptOwnerCik}).limit(1).count() == 0:
            self.collection_reporting_owner.update({'rptOwnerCik': rptOwnerCik},{'rptOwnerCik': rptOwnerCik}, upsert=True)
            self.collection_reporting_owner.update({'rptOwnerCik': rptOwnerCik}, {'$set': {'reportingOwner': {}, 'history': {}}})
        submission_date = self._convert_period_of_report(data['ownershipDocument']['periodOfReport'])
        reporting_owner_record = {}
        for reporting_owner_record in self.collection_issuer.find({'rptOwnerCik': rptOwnerCik}):
            break
        new_dict = {}
        new_dict['periodOfReport'] = submission_date
        new_dict['rptOwnerName'] = data['ownershipDocument']['reportingOwner']['reportingOwnerId']['rptOwnerName'].upper()
        new_dict['reportingOwnerAddress'] = '' 
        address_keys = ('rptOwnerStreet1', 'rptOwnerStreet2', 'rptOwnerCity', 'rptOwnerState', 'rptOwnerZipCode')
        for address_key in address_keys:
            if data['ownershipDocument']['reportingOwner']['reportingOwnerAddress'][address_key]:
                new_dict['reportingOwnerAddress'] += data['ownershipDocument']['reportingOwner']['reportingOwnerAddress'][address_key].strip() + ' '
        new_dict['reportingOwnerAddress'] = new_dict['reportingOwnerAddress'].rstrip()
        if len(reporting_owner_record['reportingOwner']) == 0: 
            self.collection_reporting_owner.update({'_id': reporting_owner_record['_id']}, {'$set': {'reportingOwner': new_dict}})
        elif reporting_owner_record['reportingOwner']['periodOfReport'] < submission_date:
            if reporting_owner_record['reportingOwner']['rptOwnerName'] != new_dict['rptOwnerName'] or
                    reporting_owner_record['reportingOwner']['reportingOwnerAddress'] != new_dict['reportingOwnerAddress']:
                historic_dict = {}
                historic_dict['rptOwnerName'] = reporting_owner_record['reportingOwner']['rptOwnerName']
                historic_dict['reportingOwnerAddress'] = reporting_owner_record['reportingOwner']['reportingOwnerAddress']
                self.collection_issuer.update({'_id': issuer_record['_id']}, {'$set': {'issuer': new_dict, 'history.'+reporting_owner_record['reportingOwner']['periodOfReport']: historic_dict }})

        return rptOwnerCik

    def _revert_unlock_slice(self,records):
        bulk = self,collection_index.initialize_ordered_bulk_op()
        for record in records:
            if self.verbose:
                print('REVERTING INDEX: '+ str(record['_id']))
            bulk.find({ '_id': record['_id'], 'processing': self.epoch_time, 'pid': os.getpid() }).update({ '$unset': { 'processing': 1, 'pid': 1 } })
        bulk.execute()

    def _select_lock_slice(self,year):
        if self.force is True:
            # Unlock all entries being processed
            self.collection_index.update({'year':year}, { '$unset': {'processing': 1, 'pid': 1}}, multi=True)
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

        # Go through records where 'rptOwnerCik'/'processing' keys are missing
        # Lock PROCESSING_BLOCK_SIZE entries in main index. 
        
        records = []
        block_size = self.PROCESSING_BLOCK_SIZE
        if self.max_records > 0:
            if self.max_record_count >= self.max_records:
                print('Reached maximum number [' + str(self.max_records) + '] of records to process; ending')
                self._record_end(year=year)
                return records
            elif self.max_records - self.max_record_count < block_size:
                block_size = self.max_records - self.max_record_count
        print('RECORD finding ['+str(block_size)+'] '+str(year))
        bulk = self.collection_index.initialize_ordered_bulk_op()
        for record in self.collection_index.find({'rptOwnerCik':{'$exists':False},'processing':{'$exists':False},'year':int(year)}).limit(block_size):
            self.max_record_count += 1
            records.append(record)
            bulk.find({ '_id': record['_id'] }).update({ '$set': { 'processing': self.epoch_time, 'pid': os.getpid() } })
        if len(records) > 0:
            bulk.execute()
        self._record_end(year=year)
        return records
