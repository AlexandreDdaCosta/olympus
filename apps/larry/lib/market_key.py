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
        chart = {}        

        output = { 'Meta': meta, 'Chart': {} }
        print(json.dumps(output,indent=4,sort_keys=True))

class Simulator(Chart):
    # Trading simulations for the Livermore Market Key.

    def __init__(self,user=USER,**kwargs):
        super(Simulator,self).__init__(user,**kwargs)

    def backtest(self,symbol=SYMBOL,**kwargs):
        pass
