#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.projects.ploutos.data.edgar import Form4

parser = ArgumentParser(sys.argv)
parser.add_argument("-a","--action",choices=['get_indexed_forms'],help="Action for this script to perform",required=True)
parser.add_argument("-f","--force",action="store_true",help="Force operation by deleting all initializations")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
parser.add_argument("-y","--year",help="Perform action only for records for the specified year")
args = parser.parse_args()

print(str(args.year))
if args.verbose is True:
    start = time.time()
process = Form4(verbose=args.verbose)
if args.action == 'get_indexed_forms':
    process.populate_indexed_forms(force=args.force,year=args.year)
if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
