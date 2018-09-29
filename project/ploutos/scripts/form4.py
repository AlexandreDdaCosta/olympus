#!/usr/bin/env python3

import time

from optparse import OptionParser

from olympus.projects.ploutos.data.edgar import Form4

parser = OptionParser()
parser.add_option("-v","--verbose",action="store_true",help="Chatty output")
args, command_string = parser.parse_args()

if args.verbose is True:
    start = time.time()
print("Begin symbol import.")
process = Form4()
if args.verbose == True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
