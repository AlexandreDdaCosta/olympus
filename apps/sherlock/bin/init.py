#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.equities_us.data.edgar import InitForm4Indices

parser = ArgumentParser(sys.argv)
parser.add_argument("-g","--graceful",action="store_true",help="Nice crash and burn for permissible errors")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose == True:
    start = time.time()
print("Begin import of EDGAR quarterly indices.")
process = InitForm4Indices(graceful=args.graceful,verbose=args.verbose)
process.populate_collections()
print("Ended import of EDGAR quarterly indices.")
if args.verbose == True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
