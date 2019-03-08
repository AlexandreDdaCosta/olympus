#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from larry.market_key import Calculate

from larry import *

parser = ArgumentParser(sys.argv)
parser.add_argument("-d","--date",default=START_CHART.strftime('%Y-%m-%d'),help="Start date for calculating chart, in format YYYY-mm-dd (e.g., 2001-01-31)")
parser.add_argument("-l","--latest",action='store_true',default=False,help="Include latest data in evaluation")
parser.add_argument("-s","--symbol",default=SYMBOL,help="US equity symbol")
parser.add_argument("-t","--thresholds",help="Overides for CONTINUATION/REVERSAL/SHORT_DISTANCE, express as an ordered list",nargs=3)
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
calculator = Calculate(args.symbol)
if args.thresholds:
    threshold = {}
    threshold['Continuation'] = args.thresholds[0]
    threshold['Reversal'] = args.thresholds[1]
    threshold['Short Distance'] = args.thresholds[2]
    thresholds = [threshold]
else:
    thresholds = THRESHOLDS
chart = calculator.chartpoints(latest=args.latest,thresholds=thresholds,start_date=args.date) 

print('CHART DATES')
for chartpoint in chart.dates:
    print(chartpoint.date + ' ' + str(chartpoint.price) + ' ' + str(chartpoint.trend))
print('UPWARD PIVOTS')
for pivot in chart.last_upward_pivot(5):
    print(pivot)
print('DOWNWARD PIVOTS')
for pivot in chart.last_downward_pivot(5):
    print(pivot)
print('RALLY PIVOTS')
for pivot in chart.last_rally_pivot(5):
    print(pivot)
print('REACTION PIVOTS')
for pivot in chart.last_reaction_pivot(5):
    print(pivot)
print('BUY SIGNALS')
for signal in chart.last_buy_signal(5):
    print(signal)
print('SELL SIGNALS')
for signal in chart.last_sell_signal(5):
    print(signal)
print('LAST ENTRY')
print(chart.last_entry())
'''
'''

if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
