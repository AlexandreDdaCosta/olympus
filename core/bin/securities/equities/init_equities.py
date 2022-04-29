#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.securities.equities.data.credentials import InitCredentials
from olympus.securities.equities.data.symbols import InitSymbols

parser = ArgumentParser(sys.argv)
parser.add_argument("-f","--force",action="store_true",help="Force reinitialization")
parser.add_argument("-g","--graceful",action="store_true",help="Nice crash and burn for permissible errors")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose == True:
    start = time.time()
print("Begin credentials set-up.")
process = InitCredentials(force=args.force,graceful=args.graceful,verbose=args.verbose)
process.populate_collections()
print("Ended credentials set-up.")
print("Begin symbol import.")
process = InitSymbols(force=args.force,graceful=args.graceful,verbose=args.verbose)
process.populate_collections()
print("Ended symbol import.")
if args.verbose == True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
