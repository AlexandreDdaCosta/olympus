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
        for date, datapoint in daily_price_series.items():
            close = float(datapoint['close'])
            high = float(datapoint['high'])
            low = float(datapoint['low'])
            if not dates:
                # Starting price (use closing price, but only to INITIATE records)
                recorded_date = { 'Date': date, 'Trend': None, 'Price': close }
                continuation, reversal = self._key_levels(datapoint)
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
                    if last_date['Trend'] == 'DOWNWARD TREND':
                        if low < last_date['Price']:
                            recorded_date['Trend'] = 'DOWNWARD TREND'
                            recorded_date['Price'] = low
                        elif high >= last_date['Price'] + reversal:
                            recorded_date['Trend'] = 'NATURAL RALLY'
                            recorded_date['Price'] = high
                            downward_pivot = {}
                            downward_pivot['Date'] = last_date['Date']
                            downward_pivot['Price'] = last_date['Price']
                            pivots['Downward'].append(downward_pivot)
                    elif last_date['Trend'] == 'UPWARD TREND':
                        pass
                    elif last_date['Trend'] == 'NATURAL RALLY':
                        pass
                    elif last_date['Trend'] == 'NATURAL REACTION':
                        pass
                    elif last_date['Trend'] == 'SECONDARY RALLY':
                        pass
                    elif last_date['Trend'] == 'SECONDARY REACTION':
                        pass

                if 'Price' in recorded_date:
                    dates.append(recorded_date)
        output = { 'Meta': meta, 'Chart': { 'Dates': dates, 'Pivots': pivots } }
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
            return CONTINUATION, REVERSAL
        return float(matching_scheme['Continuation']), float(matching_scheme['Reversal'])

class Simulator(Chart):
    # Trading simulations for the Livermore Market Key.

    def __init__(self,user=USER,**kwargs):
        super(Simulator,self).__init__(user,**kwargs)

    def backtest(self,symbol=SYMBOL,**kwargs):
        purchase_size = kwargs.get('purchase_size',PURCHASE_SIZE)
