#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.apps.larry.market_key import Calculate

from olympus.apps.larry import *

parser = ArgumentParser(sys.argv)
parser.add_argument("-s","--symbol",default=SYMBOL,help="US equity symbol")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
    calculator = Calculate(args.symbol)
    chart = calculator.chartpoints() 
    print(chart)
if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
