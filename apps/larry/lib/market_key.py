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
                continuation, reversal = self._key_levels(datapoint)
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
                        else:
                            recorded_date['Price'] = low
                            if pivots['Downward'] and low < pivots['Downward'][-1]['Price']:
                                # Added rule: Move past last downward pivot from upward trend signifies downward trend
                                recorded_date['Trend'] = 'DOWNWARD TREND'
                                signals = self._add_signal(signals,date,pivots['Downward'][-1]['Price'],'Sell','Reversal')
                            elif low <= last_date['Price'] - reversal:
                                # Rule 4.(a)/6.(a)
                                recorded_date['Trend'] = 'NATURAL REACTION'
                                pivots = self._add_pivot(pivots,last_date['Date'],last_date['Price'],'Upward')
                    elif last_date['Trend'] == 'DOWNWARD TREND':
                        if low < last_date['Price']:
                            # Rule 2
                            recorded_date['Trend'] = 'DOWNWARD TREND'
                            recorded_date['Price'] = low
                        else:
                            recorded_date['Price'] = high
                            if pivots['Upward'] and high > pivots['Upward'][-1]['Price']:
                                # Added rule: Move past last upward pivot from downward trend signifies upward trend
                                recorded_date['Trend'] = 'UPWARD TREND'
                                signals = self._add_signal(signals,date,pivots['Upward'][-1]['Price'],'Buy','Reversal')
                            elif high >= last_date['Price'] + reversal:
                                # Rule 4.(c)/6.(c)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                                pivots = self._add_pivot(pivots,last_date['Date'],last_date['Price'],'Downward')
                    elif last_date['Trend'] == 'NATURAL RALLY':
                        if high > last_date['Price']:
                            recorded_date['Price'] = high
                            if pivots['Upward'] and high >= pivots['Upward'][-1]['Price'] - short_distance and high < pivots['Upward'][-1]['Price']:
                                # Rule 10.(e)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                                recorded_date['Warning'] = 'UPWARD'
                            elif pivots['Upward'] and high > pivots['Upward'][-1]['Price']:
                                # Rule 6.(f)
                                recorded_date['Trend'] = 'UPWARD TREND'
                                signals = self._add_signal(signals,date,pivots['Upward'][-1]['Price'],'Buy','Continuation')
                            elif pivots['Rally'] and high >= pivots['Rally'][-1]['Price'] + continuation:
                                # Rule 5.(a)
                                recorded_date['Trend'] = 'UPWARD TREND'
                                signals = self._add_signal(signals,date,pivots['Rally'][-1]['Price'] + continuation,'Buy','Continuation')
                            else:
                                # Rule 6.(c)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                        else:
                            recorded_date['Price'] = low
                            if last_date['Warning'] == 'UPWARD' and low <= pivots['Rally'][-1]['Price'] - continuation:
                                # Rule 10.(e)
                                del dates[-1]['Warning']
                                signals = self._add_signal(signals,date,pivots['Rally'][-1]['Price'] - continuation,'Sell','Continuation Failure')
                            if pivots['Downward'] and low < pivots['Downward'][-1]['Price'] and low > pivots['Downward'][-1]['Price'] - continuation:
                                # Rule 10.(e)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                                recorded_date['Warning'] = 'DOWNWARD'
                            elif pivots['Downward'] and low <= pivots['Downward'][-1]['Price'] - continuation:



                        elif pivots['Downward'] and low < pivots['Downward'][-1]['Price']:
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



                    elif last_date['Trend'] == 'NATURAL REACTION':
                        pass
                    elif last_date['Trend'] == 'SECONDARY RALLY':
                        if high > last_date['Price']:
                            if pivots['Upward'] and high > pivots['Upward'][-1]['Price']:
                                # Rule 6.(d), adapted
                                recorded_date['Trend'] = 'UPWARD TREND'
                                recorded_date['Price'] = high
                                signal = {}
                                signal['Date'] = date
                                signal['Price'] = pivots['Upward'][-1]['Price']
                                signal['Type'] = 'Continuation, Secondary'
                                signals['Buy'].append(signal)
                                last_reaction = {}
                            elif high > pivots['Rally'][-1]['Price']:
                                # Rule 6.(g)
                                recorded_date['Trend'] = 'NATURAL RALLY'
                                recorded_date['Price'] = high
                                last_reaction = {}
                            else:
                                # Rule 6.(g)
                                recorded_date['Trend'] = 'SECONDARY RALLY'
                                recorded_date['Price'] = high
                        # Rules not specified
                        elif low <= last_date['Price']:
                            if pivots['Downward'] and low < pivots['Downward'][-1]['Price']:
                                # Rule 6.(b), adapted
                                recorded_date['Trend'] = 'DOWNWARD TREND'
                                recorded_date['Price'] = low
                                signal = {}
                                signal['Date'] = date
                                signal['Price'] = pivots['Downward'][-1]['Price']
                                signal['Type'] = 'Continuation, Secondary'
                                signals['Sell'].append(signal)
                                last_reaction = {}
                            elif low < last_reaction['Price']:
                                recorded_date['Trend'] = 'NATURAL REACTION'
                                recorded_date['Price'] = low
                                last_reaction = {}
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

    def _add_pivot(self,pivots,date,price,type):
        pivot = {}
        pivot['Date'] = date
        pivot['Price'] = price
        pivots[type].append(pivot)
        return pivots

    def _add_signal(self,signals,date,price,type,memo):
        signal = {}
        signal['Date'] = date
        signal['Price'] = price
        signal['Memo'] = memo
        signals[type].append(signal)
        return signals

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
