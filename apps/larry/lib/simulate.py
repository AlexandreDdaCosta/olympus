import larry.market_key as market_key

from larry import *

class Backtest(market_key.Calculate):
    # Backtest the Livermore Market Key.

    def __init__(self,symbol=SYMBOL,**kwargs):
        super(Backtest,self).__init__(symbol,**kwargs)
        self.symbol = symbol

    def simulate(self,**kwargs):
        purchase_size = kwargs.get('purchase_size',PURCHASE_SIZE)
        return self.symbol
