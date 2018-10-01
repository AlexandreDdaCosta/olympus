#!/usr/bin/env python3

import getopt, sys, time

from olympus.projects.ploutos.data.edgar import InitForm4Indices
from olympus.projects.ploutos.data.options import InitOptions
from olympus.projects.ploutos.data.symbols import InitSymbols

verbose = False
try:
    opts, args = getopt.getopt(sys.argv[1:], 'v', ['verbose'])
except getopt.GetoptError:
    print('init.py --verbose')
    sys.exit(2)
for opt, arg in opts:
    if opt in ('-v', '--verbose'):
        verbose = True

if verbose == True:
    start = time.time()
print("Begin symbol import.")
process = InitSymbols(graceful=True)
process.populate_collections()
print("Ended symbol import.")
print("Begin options import.")
process = InitOptions(graceful=True)
process.populate_collections()
print("Ended options import.")
print("Begin import of EDGAR quarterly indices.")
process = InitForm4Indices(graceful=True,verbose=verbose)
process.populate_collections()
print("Ended import of EDGAR quarterly indices.")
if verbose == True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
