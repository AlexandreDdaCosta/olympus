#!/usr/bin/env python3

import sys
import time

from argparse import ArgumentParser

from olympus.securities.equities.data.edgar import InitForm4Indices

parser = ArgumentParser(sys.argv)
parser.add_argument("-v",
                    "--verbose",
                    action="store_true",
                    help="Chatty output")
args = parser.parse_args()

if args.verbose:
    start = time.time()
print("Begin import of EDGAR quarterly indices.")
process = InitForm4Indices(verbose=args.verbose)
process.populate_collections()
print("Ended import of EDGAR quarterly indices.")
if args.verbose:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
