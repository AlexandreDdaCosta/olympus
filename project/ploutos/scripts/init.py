#!/usr/bin/env python3

from olympus.projects.ploutos.data.edgar import InitQuarterlyIndices
from olympus.projects.ploutos.data.options import InitOptions
from olympus.projects.ploutos.data.symbols import InitSymbols

print("Begin symbol import.")
#process = InitSymbols(graceful=True)
#process.populate_collections()
print("Ended symbol import.")
print("Begin options import.")
#process = InitOptions(graceful=True)
#process.populate_collections()
print("Ended options import.")
print("Begin import of EDGAR quarterly indices.")
process = InitQuarterlyIndices(graceful=True)
process.populate_collections()
print("Ended import of EDGAR quarterly indices.")
