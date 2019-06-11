#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from larry.simulate import Backtest

from larry import *

parser = ArgumentParser(sys.argv)
parser.add_argument("-l","--latest",action='store_true',default=False,help="Include latest data in evaluation")
parser.add_argument("-s","--symbol",default=SYMBOL,help="US equity symbol")
parser.add_argument("-t","--thresholds",help="Overides for CONTINUATION/REVERSAL/SHORT_DISTANCE, express as an ordered list",nargs=3)
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
backtest = Backtest(args.symbol)
if args.thresholds:
    threshold = {}
    threshold['Continuation'] = args.thresholds[0]
    threshold['Reversal'] = args.thresholds[1]
    threshold['Short Distance'] = args.thresholds[2]
    thresholds = [threshold]
else:
    thresholds = THRESHOLDS
simulation = backtest.simulate(latest=args.latest,thresholds=thresholds) 
print(simulation)

if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
