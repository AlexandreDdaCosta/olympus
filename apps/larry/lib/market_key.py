from larry import *

import olympus.equities_us.data.price as price
import olympus.equities_us.data.symbols as symbols

class Chart(object):
    # Manage charts associated with the Livermore Market Key.
    # For an example of the original Livermore paper charts, see 
    # Jesse L. Livermore, "How to Trade in Stocks, First Edition, pp. 102-133

    def __init__(self,user=USER,**kwargs):
        self.user = user

    def chartpoints(self,symbol=SYMBOL,**kwargs):
        # Given an equity symbol, will generate chart points based on the Livermore Market key
        # kwargs:
        # continuation: Threshold for CONTINUATION
        # reversal: Threshold for REVERSAL
        regen = kwargs.get('regen',False)

		# Get symbol/price data
        symbol_object = symbols.Read()
        symbol_record = symbol_object.get_symbol(symbol)
        if symbol_record is None:
            raise Exception('Symbol ' + symbol + ' not located.')
        price_object = price.Quote()
        daily_price_series = price_object.daily(symbol,regen=regen)
        if daily_price_series is None:
            raise Exception('Daily price series for ' + symbol + ' not located for date range.')
        print(daily_price_series)
        # Next: Pass date range
        # Will need to change price storage (Date, Quote)

class Simulator(Chart):
    # Trading simulations for the Livermore Market Key.

    def __init__(self,user=USER,**kwargs):
        super(Simulator,self).__init__(user,**kwargs)

    def backtest(self,symbol=SYMBOL,**kwargs):
        pass
