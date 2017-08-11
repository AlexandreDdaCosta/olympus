#!/usr/bin/env python3

from olympus.projects.ploutos.data.options import InitOptions
from olympus.projects.ploutos.data.symbols import InitSymbols

print("Begin symbol import.")
process = InitSymbols(graceful=True)
#process.populate_collections() #ALEX
print("\nEnded symbol import.")
print("Begin options import.")
process = InitOptions(graceful=True)
process.populate_collections()
print("\nEnded options import.")
