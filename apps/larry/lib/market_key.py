import json

from datetime import datetime as dt
from operator import itemgetter

import olympus.equities_us.data.price as price
import olympus.equities_us.data.symbols as symbols

from larry import *

class Chart(object):
    # Manage charts associated with the Livermore Market Key.
    # For an example of the original Livermore paper charts, see 
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition, pp. 102-133
    # Numbered rules referred to below are from Chapter 10, "Explanatory Rules", pp. 91-101

    def __init__(self,user=USER,**kwargs):
        self.user = user
        self.regen = kwargs.get('regen',False)
        self.thresholds = kwargs.get('thresholds',THRESHOLDS)

    def chartpoints(self,symbol=SYMBOL,**kwargs):
        # Given an equity symbol, will generate chart points based on the Livermore Market key
        start_date = kwargs.get('start_date',START_CHART.strftime('%Y-%m-%d'))
        end_date = kwargs.get('end_date',END_CHART.strftime('%Y-%m-%d'))
		# Get symbol/price data
        symbol_object = symbols.Read()
        symbol_record = symbol_object.get_symbol(symbol)
        if symbol_record is None:
            raise Exception('Symbol ' + symbol + ' not located.')
        price_object = price.Quote()
        daily_price_series = price_object.daily(symbol,regen=self.regen,start_date=start_date,end_date=end_date)
        if daily_price_series is None:
            raise Exception('Daily price series for ' + symbol + ' not located for date range.')
        # Create chartpoints dict
        meta = { 'Date': dt.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'Start Date': start_date, 'End Date': end_date, 'Thresholds': self.thresholds }
        # Read daily price series and populate chartpoints
        dates = []
        pivots = { 'Upward': [], 'Downward': [], 'Rally': [], 'Reaction': [] }
        signals = { 'Buy': [], 'Sell': [] }
        last_rally = {}
        last_reaction = {}
        for date, datapoint in daily_price_series.items():
            close = float(datapoint['close'])
            high = float(datapoint['high'])
            low = float(datapoint['low'])
            if not dates:
                # Starting price (use closing price, but only to INITIATE records)
                recorded_date = { 'Date': date, 'Trend': None, 'Price': close }
                continuation, reversal, short_distance = self._key_levels(datapoint)
                dates.append(recorded_date)
            else:
                last_date = dates[-1]
                continuation, reversal, short_distance = self._key_levels(datapoint)
                recorded_date = { 'Date': date }
                if len(dates) == 1:
                    # Starting trend
                    if close > last_date['Price']:
                        recorded_date['Trend'] = 'UPWARD TREND'
                        recorded_date['Price'] = high
                    elif close < last_date['Price']:
                        recorded_date['Trend'] = 'DOWNWARD TREND'
                        recorded_date['Price'] = low
                else:
                    if last_date['Trend'] == 'UPWARD TREND':
                        if high > last_date['Price']:
                            # Rule 1 
                            recorded_date['Trend'] = 'UPWARD TREND'
                            recorded_date['Price'] = high
                            if 'Unconfirmed' in last_date:
                                if high >= pivots['Upward'][-1]['Price'] + continuation:
                                    # Rule 10.(a)
                                    signal = {}
                                    signal['Date'] = date
                                    signal['Price'] = pivots['Upward'][-1]['Price'] + continuation
                                    signal['Type'] = 'Continuation'
                                    signals['Buy'].append(signal)
                                else:
                                    recorded_date['Unconfirmed'] = 'True'
                        else:
                            if 'Unconfirmed' in last_date and low <= pivots['Upward'][-1]['Price'] - continuation:
                                # Rule 10.(b)
                                signal = {}
                                signal['Date'] = date
                                signal['Price'] = pivots['Upward'][-1]['Price'] - continuation
                                signal['Type'] = 'Failed Confirmation'
                                signals['Sell'].append(signal)
                                del dates[-1]['Unconfirmed']
                            if pivots['Downward'] and low < pivots['Downward'][-1]['Price']:
                                # Larry rule: Move past last downward pivot from upward trend signifies downward trend
                                recorded_date['Trend'] = 'DOWNWARD TREND'
                                recorded_date['Price'] = low
                                if low > pivots['Downward'][-1]['Price'] - continuation:
                                    recorded_date['Unconfirmed'] = 'True'
                                else:
                                    signal = {}
                                    signal['Date'] = date
                                    signal['Price'] = pivots['Downward'][-1]['Price'] - continuation
                                    signal['Type'] = 'Reversal'
                                    signals['Sell'].append(signal)
                            elif low <= last_date['Price'] - reversal:
                                # Rule 4.(a)/6.(a)
                                recorded_date['Trend'] = 'NATURAL REACTION'
                                recorded_date['Price'] = low
                                pivot = {}
                                pivot['Date'] = last_date['Date']
                                pivot['Price'] = last_date['Price']
                                pivots['Upward'].append(pivot)
                    elif last_date['Trend'] == 'DOWNWARD TREND':
                        if low < last_date['Price']:
                            # Rule 2
                            recorded_date['Trend'] = 'DOWNWARD TREND'
                            recorded_date['Price'] = low
                            if 'Unconfirmed' in last_date:
                                if low <= pivots['Downward'][-1]['Price'] - continuation:
                                    # Rule 10.(c)
                                    signal = {}
                                    signal['Date'] = date
                                    signal['Price'] = pivots['Downward'][-1]['Price'] - continuation
                                    signal['Type'] = 'Continuation'
                                    signals['Sell'].append(signal)
                                else:
                                    recorded_date['Unconfirmed'] = 'True'
                        else:
                            if 'Unconfirmed' in last_date and high >= pivots['Downward'][-1]['Price'] + continuation:
                                # Rule 10.(d)
                                signal = {}
                                signal['Date'] = date
                                signal['Price'] = pivots['Downward'][-1]['Price'] + continuation
                                signal['Type'] = 'Failed Confirmation'
                                signals['Buy'].append(signal)
                                del dates[-1]['Unconfirmed']
                            if pivots['Upward'] and high > pivots['Upward'][-1]['Price']:
                                # Larry rule: Move past last upward pivot from downward trend signifies upward trend
                                recorded_date['Trend'] = 'UPWARD TREND'
                                recorded_date['Price'] = high
                                if high < pivots['Upward'][-1]['Price'] + continuation:
                                    recorded_date['Unconfirmed'] = 'True'
                                else:
                                    signal = {}
                                    signal['Date'] = date
                                    signal['Price'] = pivots['Upward'][-1]['Price'] + continuation
                                    signal['Type'] = 'Reversal'
                                    signals['Buy'].append(signal)
                            elif high >= last_date['Price'] + reversal:
                                # Rule 4.(c)/6.(c)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                                recorded_date['Price'] = high
                                pivot = {}
                                pivot['Date'] = last_date['Date']
                                pivot['Price'] = last_date['Price']
                                pivots['Downward'].append(pivot)
                    # Rule 3 (all remaining cases)
                    elif last_date['Trend'] == 'NATURAL RALLY':
                        if high > last_date['Price']:
                            if pivots['Upward'] and high > pivots['Upward'][-1]['Price']:
                                # Rule 6.(f)
                                recorded_date['Trend'] = 'UPWARD TREND'
                                if high < pivots['Upward'][-1]['Price'] + continuation:
                                    recorded_date['Unconfirmed'] = 'True'
                                else:
                                    signal = {}
                                    signal['Date'] = date
                                    signal['Price'] = pivots['Upward'][-1]['Price'] + continuation
                                    signal['Type'] = 'Continuation'
                                    signals['Buy'].append(signal)
                            elif pivots['Upward'] and high > pivots['Upward'][-1]['Price'] - short_distance:
                                # Rule 6.(c)/10.(e)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                                recorded_date['Unconfirmed'] = 'True'
                            else:
                                # Rule 6.(c)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                            recorded_date['Price'] = high
                        else:
                            if 'Unconfirmed' in last_date and low <= pivots['Upward'][-1]['Price'] - continuation:
                                # Rule 10.(e)
                                signal = {}
                                signal['Date'] = date
                                signal['Price'] = pivots['Upward'][-1]['Price'] - continuation
                                signal['Type'] = 'Failed Confirmation'
                                signals['Sell'].append(signal)
                                del dates[-1]['Unconfirmed']



'''

                            if pivots['Downward'] and low < pivots['Downward'][-1]['Price']:
                                # Rule 6.(b)
                                recorded_date['Price'] = low
                                recorded_date['Trend'] = 'DOWNWARD TREND'
                                pivot = {}
                                pivot['Date'] = last_date['Date']
                                pivot['Price'] = last_date['Price']
                                pivots['Rally'].append(pivot)

                        # Rule 4.(d)
                        elif low < last_date['Price'] - reversal:
                            elif pivots['Reaction'] and low > pivots['Reaction'][-1]['Price']:
                                # Rule 6.(h)
                                recorded_date['Trend'] = 'SECONDARY REACTION'
                                last_rally = {}
                                last_rally['Date'] = date
                                last_rally['Price'] = high
                            else:
                                recorded_date['Trend'] = 'NATURAL REACTION'
                                pivot = {}
                                pivot['Date'] = last_date['Date']
                                pivot['Price'] = last_date['Price']
                                pivots['Rally'].append(pivot)
                            recorded_date['Price'] = low
'''

                    elif last_date['Trend'] == 'NATURAL REACTION':
                        pass
                    elif last_date['Trend'] == 'SECONDARY RALLY':
                        pass
                    elif last_date['Trend'] == 'SECONDARY REACTION':
                        pass

                if 'Price' in recorded_date and 'Trend' in recorded_date:
                    dates.append(recorded_date)
        output = { 'Meta': meta, 'Chart': { 'Dates': dates, 'Pivots': pivots, 'Signals': signals } }
        # Save for potential reuse
        print(continuation)
        print(reversal)
        print(json.dumps(output,indent=4,sort_keys=True))
        #return output

    def _key_levels(self,datapoint):
        # Calculates continuation and reversal amounts based on pricing
        matching_scheme = None
        minimum = 0
        for scheme in sorted(self.thresholds, key=itemgetter('Continuation')) :
            if float(datapoint['close']) > minimum and ('Maximum' not in scheme or float(datapoint['close']) <= float(scheme['Maximum'])):
                matching_scheme = scheme
                break
            minimum = scheme['Maximum']
        if matching_scheme is None:
            return CONTINUATION, REVERSAL, SHORT_DISTANCE
        return float(matching_scheme['Continuation']), float(matching_scheme['Reversal']), float(matching_scheme['Short Distance'])

class Simulator(Chart):
    # Trading simulations for the Livermore Market Key.

    def __init__(self,user=USER,**kwargs):
        super(Simulator,self).__init__(user,**kwargs)

    def backtest(self,symbol=SYMBOL,**kwargs):
        purchase_size = kwargs.get('purchase_size',PURCHASE_SIZE)
