#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.projects.ploutos.data.edgar import Form4

parser = ArgumentParser(sys.argv)
parser.add_argument("-a","--action",choices=['get_indexed_forms'],help="Action for this script to perform",required=True)
parser.add_argument("-f","--force",action="store_true",help="Force operation by deleting all initializations")
parser.add_argument("-i","--identifier",help="A record identifier; for processing individual records, by action")
parser.add_argument("-m","--max_records",default=0,help="Maximum number of records to process, by action. 0 or less == no maximum.",type=int)
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
parser.add_argument("-y","--year",help="Perform action only for records for the specified year")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
process = Form4(verbose=args.verbose)
if args.action == 'get_indexed_forms':
    # Here identifier == cik (issuer of security) + '-' + EDGAR file name, minus suffix
    process.populate_indexed_forms(force=args.force,cik_file=args.identifier,max_records=args.max_records,year=args.year)
if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
