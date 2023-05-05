import datetime
import edgar as form4_index_downloader
import json
import os
import re
import shutil
import time
import wget
import xmlschema
import xmltodict
import xml.etree.ElementTree as ET

from bson.json_util import dumps, loads
from xmlschema.validators.exceptions import XMLSchemaValidationError

import olympus.securities.equities.data as data

from olympus import USER

FORM4_INDEX_COLLECTION_NAME = 'edgar'
QUARTERLY_FIRST_YEAR = 2004
QUARTERLY_ORIGINAL_YEAR = 1993
QUARTERLY_YEAR_LIST = range(QUARTERLY_FIRST_YEAR,datetime.datetime.now().year+1)

class InitForm4Indices(data.Initializer):

    def __init__(self, username=USER, **kwargs):
        super(InitForm4Indices,self).__init__(FORM4_INDEX_COLLECTION_NAME,username,**kwargs)

    def populate_collections(self):
        self.prepare()
        if self.verbose:
            print('Initializing Form4 collection procedure.')
       
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

        shutil.rmtree(download_directory)
        self.clean_up()

class Form4(data.Connection):

    FORM4_SUBMISSIONS_COLLECTION_NAME = 'form4_submissions'
    ISSUER_COLLECTION_NAME = 'form4_issuer'
    REPORTING_OWNER_COLLECTION_NAME = 'form4_reporting_owner'
    INIT_SLEEP = 5
    INIT_WAIT = 20
    PROCESSING_BLOCK_SIZE = 100

    def __init__(self,username=USER,**kwargs):
        super(Form4,self).__init__(username,**kwargs)

    def populate_indexed_forms(self,**kwargs):

        # Gather detailed Form4 records based on downloaded EDGAR indices
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
  
        self.done = False
        self.force_unlocked = False

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
                if self.done:
                    break
                records = self._select_lock_slice(year)
                if len(records) == 0:
                    if self.verbose and not self.done:
                        print('No unprocessed index entries found for '+str(year)+'; ending.')
                    break
                self._get_write_forms(year,records)
        else:
            for year in QUARTERLY_YEAR_LIST:
                if self.done:
                    break
                while True:
                    if self.done:
                        break
                    records = self._select_lock_slice(year)
                    if len(records) == 0:
                        if self.verbose:
                            print('No unprocessed index entries found for '+str(year)+'; skipping.')
                        break
                    self._get_write_forms(year,records)

    def _convert_period_of_report(self, submission_date):
        year, month, day = str(submission_date).split('-')
        t = datetime.datetime(int(year), int(month), int(day), 0, 0)
        return int(time.mktime(t.timetuple()))

    def _extract_transaction(self,transaction):
        #ALEX
        '''
        <derivativeTransaction>
            <securityTitle>
                <value>Incentive Stock Option (right to buy)</value>
            </securityTitle>
            <conversionOrExercisePrice>
                <value>1.9</value>
            </conversionOrExercisePrice>
            <transactionDate>
                <value>2004-01-05</value>
            </transactionDate>
            <transactionCoding>
                <transactionFormType>4</transactionFormType>
                <transactionCode>M</transactionCode>
                <equitySwapInvolved>0</equitySwapInvolved>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>2000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>0</value>
                </transactionPricePerShare>
                <transactionAcquiredDisposedCode>
                    <value>D</value>
                </transactionAcquiredDisposedCode>
            </transactionAmounts>
            <exerciseDate>
                <footnoteId id="F1"/>
            </exerciseDate>
            <expirationDate>
                <value>2011-09-24</value>
            </expirationDate>
            <underlyingSecurity>
                <underlyingSecurityTitle>
                    <value>Common Stock</value>
                </underlyingSecurityTitle>
                <underlyingSecurityShares>
                    <value>2000</value>
                </underlyingSecurityShares>
            </underlyingSecurity>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction>
                    <value>2000</value>
                </sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership>
                    <value>D</value>
                </directOrIndirectOwnership>
            </ownershipNature>
        </derivativeTransaction>
        '''
        return 1

    def _fix_xml_content(self,xml_content,e):
        XML = ET.fromstring(xml_content)
        if e.reason == "invalid datetime for formats ('%Y-%m-%d', '-%Y-%m-%d').":
            path = e.path
            path = re.sub(r'^(\/.*?)(\/.*)$',r'\g<2>',e.path)
            for i in XML.findall('.'+path):
                text = re.sub(r"[\s\-]", "", i.text, flags=re.UNICODE)
                text = text[:4] + '-' + text[4:6] + '-' + text[6:8]
                i.text = text
        else:
            return None
        return ET.tostring(XML)

    def _get_write_forms(self,year,records):
        download_directory = '/tmp/form4_submissions_'+str(os.getpid())+'_'+str(self.epoch_time)+'/'
        if not os.path.isdir(download_directory):
            os.mkdir(download_directory)
        for record in records:
            try:
                url = 'https://www.sec.gov/Archives/edgar/data/'+str(record['issuerCik'])+'/'+record['file']+'.txt'
                if self.verbose:
                    print(url)
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
                
                # Fix CRLF problems due to run-on lines
                xml_content = xml_content.replace("\n", "")
               
                xml_validate = True 
                repair_attempts = 0
                while xml_validate is True:
                    try:
                        if record['form'] == '4/A':
                            xmlschema.validate(xml_content,schema=self.form4a_schema)
                        else:
                            xmlschema.validate(xml_content,schema=self.form4_schema)
                    except XMLSchemaValidationError as e:
                        repair_attempts += 1
                        if repair_attempts <= 10:
                            xml_content = self._fix_xml_content(xml_content,e)
                        else:
                            xml_content = None
                        if xml_content is None:
                            if self.verbose:
                                print('\n\nhttps://www.sec.gov/Archives/edgar/data/'+str(record['issuerCik'])+'/'+record['file']+'.txt\n')
                                print('Gracefully bypassing record ' + str(record['_id']) + ' for failed validation:\n'+str(e))
                            raise
                    except Exception:
                        raise
                    xml_validate = False
                data = {}
                data = xmltodict.parse(xml_content)

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
                    if issuer_record['issuer']['issuerName'] != new_dict['issuerName'] or issuer_record['issuer']['issuerTradingSymbol'] != new_dict['issuerTradingSymbol']:
                        historic_dict = {}
                        historic_dict['issuerName'] = issuer_record['issuer']['issuerName']
                        historic_dict['issuerTradingSymbol'] = issuer_record['issuer']['issuerTradingSymbol']
                        self.collection_issuer.update({'_id': issuer_record['_id']}, {'$set': {'issuer': new_dict, 'history.'+str(issuer_record['issuer']['periodOfReport']): historic_dict }})

                # reportingOwner document + submission data
                owner_cik = []
                if type(data['ownershipDocument']['reportingOwner']) is list:
                    for reportingOwner in data['ownershipDocument']['reportingOwner']:
                        rptOwnerCik = self._reporting_owner_handler(data,record,reportingOwner)
                        owner_cik.append(rptOwnerCik)
                else:
                    rptOwnerCik = self._reporting_owner_handler(data,record)
                    owner_cik.append(rptOwnerCik)
                # Form4 index
                self.collection_index.update({'issuerCik':record['issuerCik'], 'file':record['file']}, {'$set': { 'rptOwnerCik': owner_cik }, '$unset': { 'failure': 1, 'processing': 1, 'pid': 1 }} )
                if self.verbose:
                    print('UPDATED INDEX: '+ str(record['issuerCik']) + ' ' + str(record['file']))

            except Exception as e:
                if os.path.isdir(download_directory):
                    shutil.rmtree(download_directory)
                self._revert_unlock_slice(records,record['_id'],str(e))
                raise
        if os.path.isdir(download_directory):
            shutil.rmtree(download_directory)

    def _reporting_owner_handler(self,data,record,reporting_owner=None):
        if reporting_owner is not None:
            reporting_owner_dict = reporting_owner
        else:
            reporting_owner_dict = data['ownershipDocument']['reportingOwner']
        rptOwnerCik = int(reporting_owner_dict['reportingOwnerId']['rptOwnerCik'])
        if self.collection_submissions.find({'rptOwnerCik': rptOwnerCik}).limit(1).count() == 0:
            self.collection_submissions.update({'rptOwnerCik':rptOwnerCik},{'rptOwnerCik':rptOwnerCik, 'issuerCik':{}}, upsert=True)

        # Populate submission data structures

        reportingOwner = {}
        if 'reportingOwnerRelationship' in reporting_owner_dict:
            relationship_keys = ('isDirector','isOfficer','isTenPercentOwner')
            for key in relationship_keys:
                if key in reporting_owner_dict['reportingOwnerRelationship'] and str(reporting_owner_dict['reportingOwnerRelationship'][key].strip()) == '1':
                    reportingOwner[key] = True
            if 'officerTitle' in reporting_owner_dict['reportingOwnerRelationship']:
                officer_title = reporting_owner_dict['reportingOwnerRelationship']['officerTitle'].strip()
                if officer_title:
                    reportingOwner['officerTitle'] = officer_title

        nonDerivativeTransaction = []
        if 'nonDerivativeTable' in data['ownershipDocument'] and 'nonDerivativeTransaction' in data['ownershipDocument']['nonDerivativeTable'] and data['ownershipDocument']['nonDerivativeTable']['nonDerivativeTransaction']:
            print('nonDerivativeTransaction')
            if type(data['ownershipDocument']['nonDerivativeTable']['nonDerivativeTransaction']) is not list:
                nonDerivativeTransaction.append(self._extract_transaction(data['ownershipDocument']['nonDerivativeTable']['nonDerivativeTransaction']))
            else:
                print('LIST')
                for transaction in data['ownershipDocument']['nonDerivativeTable']['nonDerivativeTransaction']:
                    nonDerivativeTransaction.append(self._extract_transaction(transaction))

        derivativeTransaction = []
        if 'derivativeTable' in data['ownershipDocument'] and 'derivativeTransaction' in data['ownershipDocument']['derivativeTable'] and data['ownershipDocument']['derivativeTable']['derivativeTransaction']:
            print('derivativeTransaction')
            if type(data['ownershipDocument']['derivativeTable']['derivativeTransaction']) is not list:
                derivativeTransaction.append(self._extract_transaction(data['ownershipDocument']['derivativeTable']['derivativeTransaction']))
            else:
                for transaction in data['ownershipDocument']['derivativeTable']['derivativeTransaction']:
                    derivativeTransaction.append(self._extract_transaction(transaction))

        self.collection_submissions.update({'rptOwnerCik':rptOwnerCik}, {'$set': {'issuerCik.'+str(record['issuerCik'])+'.'+record['file']: { 'reportingOwner': reportingOwner, 'nonDerivativeTransaction': nonDerivativeTransaction, 'derivativeTransaction': derivativeTransaction }}})
        if self.verbose:
            print('VERIFIED CIK OWNER: '+ str(rptOwnerCik))

        # Parse/add/update reporting owner data
        if self.collection_reporting_owner.find({'rptOwnerCik': rptOwnerCik}).limit(1).count() == 0:
            self.collection_reporting_owner.update({'rptOwnerCik': rptOwnerCik},{'rptOwnerCik': rptOwnerCik}, upsert=True)
            self.collection_reporting_owner.update({'rptOwnerCik': rptOwnerCik}, {'$set': {'reportingOwner': {}, 'history': {}}})
        submission_date = self._convert_period_of_report(data['ownershipDocument']['periodOfReport'])
        reporting_owner_record = {}
        for reporting_owner_record in self.collection_reporting_owner.find({'rptOwnerCik': rptOwnerCik}):
            break
        new_dict = {}
        new_dict['periodOfReport'] = submission_date
        if reporting_owner is not None:
            new_dict['rptOwnerName'] = reporting_owner['reportingOwnerId']['rptOwnerName'].upper()
        else:
            new_dict['rptOwnerName'] = data['ownershipDocument']['reportingOwner']['reportingOwnerId']['rptOwnerName'].upper()
        new_dict['reportingOwnerAddress'] = '' 
        address_keys = ('rptOwnerStreet1', 'rptOwnerStreet2', 'rptOwnerCity', 'rptOwnerState', 'rptOwnerZipCode')
        for address_key in address_keys:
            if reporting_owner is not None and 'reportingOwnerAddress' in reporting_owner:
                if (
                       address_key in reporting_owner['reportingOwnerAddress'] 
                       and reporting_owner['reportingOwnerAddress'][address_key] is not None
                   ):
                    new_dict['reportingOwnerAddress'] += reporting_owner['reportingOwnerAddress'][address_key].strip() + ' '
            elif 'reportingOwnerAddress' in data['ownershipDocument']['reportingOwner']:
                if (
                       address_key in data['ownershipDocument']['reportingOwner']['reportingOwnerAddress'] 
                       and data['ownershipDocument']['reportingOwner']['reportingOwnerAddress'][address_key] is not None
                   ):
                    new_dict['reportingOwnerAddress'] += data['ownershipDocument']['reportingOwner']['reportingOwnerAddress'][address_key].strip() + ' '
        new_dict['reportingOwnerAddress'] = new_dict['reportingOwnerAddress'].rstrip()
        if len(reporting_owner_record['reportingOwner']) == 0: 
            self.collection_reporting_owner.update({'_id': reporting_owner_record['_id']}, {'$set': {'reportingOwner': new_dict}})
        elif reporting_owner_record['reportingOwner']['periodOfReport'] < submission_date:
            if (
                   reporting_owner_record['reportingOwner']['rptOwnerName'] != new_dict['rptOwnerName']
                   or ('reportingOwnerAddress' in reporting_owner_record['reportingOwner'] and reporting_owner_record['reportingOwner']['reportingOwnerAddress'] != new_dict['reportingOwnerAddress'])
                   or 'reportingOwnerAddress' not in reporting_owner_record['reportingOwner']
               ):
                historic_dict = {}
                historic_dict['rptOwnerName'] = reporting_owner_record['reportingOwner']['rptOwnerName']
                if 'reportingOwnerAddress' in reporting_owner_record['reportingOwner']:
                    historic_dict['reportingOwnerAddress'] = reporting_owner_record['reportingOwner']['reportingOwnerAddress']
                self.collection_reporting_owner.update({'_id': reporting_owner_record['_id']}, {'$set': {'reportingOwner': new_dict, 'history.'+str(reporting_owner_record['reportingOwner']['periodOfReport']): historic_dict }})

        return rptOwnerCik

    def _revert_unlock_record(self,id,error):
        self.collection_index.update({'_id': id}, { '$set': { 'failure': error }, '$unset': {'processing': 1, 'pid': 1}})
        if self.verbose:
            print('UNLOCK CHECK FOR SINGLE INDEX ENTRY: '+ str(id))
        self.max_record_count -= 1
        self.done = False

    def _revert_unlock_slice(self,records,id,error):
        bulk = self.collection_index.initialize_ordered_bulk_op()
        for record in records:
            bulk.find({ '_id': record['_id'], 'processing': self.epoch_time, 'pid': os.getpid() }).update({ '$unset': { 'failure': 1, 'processing': 1, 'pid': 1 }})
            if self.verbose:
                print('UNLOCK CHECK FOR INDEX ENTRY: '+ str(record['_id']))
        bulk.execute()
        self.collection_index.update({'_id': id}, { '$set': { 'failure': error }})

    def _select_lock_slice(self,year):
        if self.done is True:
            return []
        if not self.force_unlocked:
            # Unlock all entries being processed and all failed entries
            print('FORCING '+str(year))
            self.collection_index.update({ 'failure': { '$exists': True }, 'year': int(year)}, {'$unset': {'failure': 1}}, multi=True)
            self.collection_index.update({ 'pid': { '$exists': True }, 'year': int(year)}, {'$unset': {'pid': 1, 'processing': 1}}, multi=True)
            self.force_unlocked = True

        # Go through records where 'rptOwnerCik'/'processing' keys are missing
        # Lock PROCESSING_BLOCK_SIZE entries in main index. 
        
        records = []
        block_size = self.PROCESSING_BLOCK_SIZE
        if self.max_records > 0:
            if self.max_record_count >= self.max_records:
                print('Reached maximum number [' + str(self.max_records) + '] of records to process; ending')
                self.done = True
                return records
            elif self.max_records - self.max_record_count < block_size:
                block_size = self.max_records - self.max_record_count
                self.done = True
        print('RECORD finding ['+str(block_size)+'] '+str(year))
        bulk = self.collection_index.initialize_ordered_bulk_op()
        for record in self.collection_index.find({'rptOwnerCik':{'$exists':False},'failure':{'$exists':False},'processing':{'$exists':False},'year':int(year)}).limit(block_size):
            self.max_record_count += 1
            records.append(record)
            bulk.find({ '_id': record['_id'] }).update({ '$set': { 'processing': self.epoch_time, 'pid': os.getpid() } })
        if len(records) > 0:
            bulk.execute()
        return records
