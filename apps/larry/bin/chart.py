#!/usr/bin/env python3

import sys, time

from argparse import ArgumentParser

from larry.market_key import Calculate

from larry import *

parser = ArgumentParser(sys.argv)
parser.add_argument("-d","--date",default=START_CHART.strftime('%Y-%m-%d'),help="Start date for calculating chart")
parser.add_argument("-r","--real_time",action='store_true',default=False,help="Include real-time data in evaluation")
parser.add_argument("-s","--symbol",default=SYMBOL,help="US equity symbol")
parser.add_argument("-v","--verbose",action="store_true",help="Chatty output")
args = parser.parse_args()

if args.verbose is True:
    start = time.time()
calculator = Calculate(args.symbol)
chart = calculator.chartpoints(real_time=args.real_time,start_date=args.date) 

'''
for chartpoint in chart.dates:
    print(chartpoint.date + ' ' + str(chartpoint.price) + ' ' + str(chartpoint.trend))
print(chart.last_entry())
print(chart.last_upward_pivot())
print(chart.last_downward_pivot())
print(chart.last_rally_pivot())
print(chart.last_reaction_pivot())
print(chart.last_sell_signal())
for signal in chart.last_buy_signal(all=True):
    print(signal)
'''

if args.verbose is True:
    end = time.time()
    print('Elapsed seconds: ' + str(end - start))
