#!/usr/bin/env python3

import sys
import time

from argparse import ArgumentParser

from olympus.securities.equities.data.symbols import InitSymbols

parser = ArgumentParser(sys.argv)
parser.add_argument("-v",
                    "--verbose",
                    action="store_true",
                    help="Chatty output")
args = parser.parse_args()

if args.verbose:
    start = time.time()
print("Begin symbol import.")
process = InitSymbols(verbose=args.verbose)
process.populate_collections()
process.post_populate_collections()
print("Ended symbol import.")
if args.verbose:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
