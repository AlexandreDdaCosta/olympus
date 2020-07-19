#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from larry import *
from larry.simulate import Backtest
from olympus.equities_us import SYMBOL

parser = ArgumentParser(sys.argv)
parser.add_argument("-s","--symbol",default=SYMBOL,help="US equity symbol")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
backtest = Backtest(args.symbol)
simulation = backtest.simulate()

if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
