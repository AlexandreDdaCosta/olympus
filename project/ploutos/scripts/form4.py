#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.projects.ploutos.data.edgar import Form4

parser = ArgumentParser(sys.argv)
parser.add_argument("-a","--action",choices=['get_indexed_forms'],help="Action for this script to perform",required=True)
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
process = Form4()

if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
