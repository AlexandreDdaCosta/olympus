#!/usr/bin/env python3

from olympus.projects.ploutos.data.options import InitOptions
from olympus.projects.ploutos.data.symbols import InitSymbols

print("Begin symbol import.")
process = InitSymbols()
process.populate_collections()
print("\nEnded symbol import.")
print("Begin options import.")
process = InitOptions()
process.populate_collections()
print("\nEnded options import.")
