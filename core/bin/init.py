#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.equities_us.data.options import InitOptions
from olympus.equities_us.data.symbols import InitSymbols

parser = ArgumentParser(sys.argv)
parser.add_argument("-g","--graceful",action="store_true",help="Nice crash and burn for permissible errors")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose == True:
    start = time.time()
print("Begin symbol import.")
process = InitSymbols(graceful=args.graceful,verbose=args.verbose)
process.populate_collections()
print("Ended symbol import.")
print("Begin options import.")
process = InitOptions(graceful=args.graceful,verbose=args.verbose)
process.populate_collections()
print("Ended options import.")
if args.verbose == True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))