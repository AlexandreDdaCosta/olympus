#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from olympus.securities.equities.algo.market_key import *
from olympus.securities.equities.algo.market_key.livermore import Calculate
from olympus.securities.equities import BUY, SELL, SYMBOL

parser = ArgumentParser(sys.argv)
parser.add_argument("-i","--interval",default='1d',help="Quotes intervals for which to produce the chart")
parser.add_argument("-l","--latest",action='store_true',default=False,help="Include latest data in evaluation")
parser.add_argument("-s","--symbol",default=SYMBOL,help="US equity symbol")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
calculator = Calculate()
chart = calculator.chartpoints(args.symbol,args.interval,latest=args.latest)

if chart.last_entry():
    print('CHART DATES')
    #'''
    for chartpoint in chart.dates:
        print(chartpoint)
    print('UPWARD PIVOTS')
    if chart.has_pivot(UPWARD_TREND) is True:
        for pivot in chart.last_upward_pivot(all=True):
            print(pivot)
    print('DOWNWARD PIVOTS')
    if chart.has_pivot(DOWNWARD_TREND) is True:
        for pivot in chart.last_downward_pivot(all=True):
            print(pivot)
    print('RALLY PIVOTS')
    if chart.has_pivot(NATURAL_RALLY) is True:
        for pivot in chart.last_rally_pivot(all=True):
            print(pivot)
    print('REACTION PIVOTS')
    if chart.has_pivot(NATURAL_REACTION) is True:
        for pivot in chart.last_reaction_pivot(all=True):
            print(pivot)
    print('BUY SIGNALS')
    if chart.has_signal(BUY) is True:
        for signal in chart.last_buy_signal(all=True):
            print(signal)
    print('SELL SIGNALS')
    if chart.has_signal(SELL) is True:
        for signal in chart.last_sell_signal(all=True):
            print(signal)
    print('LAST ENTRY')
    print(chart.last_entry())
    #'''
else:
    raise Exception('Empty chart')
if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
