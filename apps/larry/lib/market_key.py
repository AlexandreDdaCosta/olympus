import json

from datetime import datetime as dt

import olympus.equities_us.data.price as price
import olympus.equities_us.data.symbols as symbols

from larry import *

class Chart(object):
    # Manage charts associated with the Livermore Market Key.
    # For an example of the original Livermore paper charts, see 
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition, pp. 102-133

    def __init__(self,user=USER,**kwargs):
        self.user = user

    def chartpoints(self,symbol=SYMBOL,**kwargs):
        # Given an equity symbol, will generate chart points based on the Livermore Market key
        regen = kwargs.get('regen',False)
        start_date = kwargs.get('start_date',START_CHART.strftime('%Y-%m-%d'))
        end_date = kwargs.get('end_date',END_CHART.strftime('%Y-%m-%d'))
		# Get symbol/price data
        symbol_object = symbols.Read()
        symbol_record = symbol_object.get_symbol(symbol)
        if symbol_record is None:
            raise Exception('Symbol ' + symbol + ' not located.')
        price_object = price.Quote()
        daily_price_series = price_object.daily(symbol,regen=regen,start_date=start_date,end_date=end_date)
        if daily_price_series is None:
            raise Exception('Daily price series for ' + symbol + ' not located for date range.')
        # Create chartpoints dict
        meta = { 'Date': dt.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'Start Date': start_date, 'End Date': end_date }
        # Read daily price series and populate chartpoints
        dates = []
        data = { 'Last Highs': [], 'Last Lows': [] }
        for date, datapoint in daily_price_series.items():
            if not dates:
                # Starting price (use closing price, but only to INITIATE records)
                recorded_date = { 'Date': date, 'Trend': None, 'Price': datapoint['close'] }
                dates.append(recorded_date)
            else:
                last_date = dates[-1]
                continuation, reversal = self._key_levels(datapoint,data)
                recorded_date = { 'Date': date }
                if len(dates) == 1:
                    # Starting trend
                    if datapoint['close'] > last_date['Price']:
                        recorded_date['Trend'] = 'UPWARD_TREND'
                        recorded_date['Price'] = datapoint['high']
                    elif datapoint['close'] < last_date['Price']:
                        recorded_date['Trend'] = 'DOWNWARD_TREND'
                        recorded_date['Price'] = datapoint['low']

                if 'Price' in recorded_date:
                    dates.append(recorded_date)
                data['Continuation'] = continuation
                data['Reversal'] = reversal
            data['Last Highs'].append(datapoint['high'])
            data['Last Lows'].append(datapoint['low'])
            if len(data['Last Highs']) > 3:
                data['Last Highs'].pop(0)
            if len(data['Last Lows']) > 3:
                data['Last Lows'].pop(0)
        output = { 'Meta': meta, 'Chart': { 'Dates': dates, 'Data': data } }
        # Save for potential reuse


        print(json.dumps(output,indent=4,sort_keys=True))
        #return output

    def _key_levels(self,datapoint,data):
        # Calculates continuation and reversal amounts based on pricing
        continuation = 1
        reversal = 2
        if float(datapoint['high']) > 20:
            pass
        return continuation, reversal

class Simulator(Chart):
    # Trading simulations for the Livermore Market Key.

    def __init__(self,user=USER,**kwargs):
        super(Simulator,self).__init__(user,**kwargs)

    def backtest(self,symbol=SYMBOL,**kwargs):
        pass
