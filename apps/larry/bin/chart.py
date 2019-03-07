#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from larry.market_key import Calculate

from larry import *

parser = ArgumentParser(sys.argv)
parser.add_argument("-s","--symbol",default=SYMBOL,help="US equity symbol")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
calculator = Calculate(args.symbol)
chart = calculator.chartpoints() 

print(chart.last_entry())
print(chart.last_upward_pivot())
print(chart.last_downward_pivot())
print(chart.last_rally_pivot())
print(chart.last_reaction_pivot())
print(chart.last_sell_signal())
for signal in chart.last_buy_signal(all=True):
    print(signal)

if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
