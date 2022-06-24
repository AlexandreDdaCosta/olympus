#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.securities.equities.data.credentials import InitCredentials
from olympus.securities.equities.data.symbols import InitSymbols

parser = ArgumentParser(sys.argv)
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose == True:
    start = time.time()
print("Begin credentials set-up.")
# ALEX process = InitCredentials(verbose=args.verbose)
# process.populate_collections()
print("Ended credentials set-up.")
print("Begin symbol import.")
process = InitSymbols(verbose=args.verbose)
process.populate_collections()
print("Ended symbol import.")
if args.verbose == True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
