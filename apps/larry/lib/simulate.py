import larry.market_key as market_key

from larry import *

class Backtest(market_key.Calculate):
    # Backtest the Livermore Market Key.

    def __init__(self,symbol=SYMBOL,**kwargs):
        super(Backtest,self).__init__(symbol,**kwargs)
        self.symbol = symbol

    def simulate(self,**kwargs):
        purchase_size = kwargs.get('purchase_size',PURCHASE_SIZE)
        # ALEX steps
        # Create rotation object to change parameters for each run
        # For each set of parameters:
        #   Create a chart
        chart = self.chartpoints()
        #   Calculate performance based on buy/sell signals
        if first_buy = chart.first_buy_signal(BUY) is not None:
            
            for signal in chart.last_buy_signal(all=True):
                print(signal)
        if chart.has_signal(SELL) is True:
            for signal in chart.last_sell_signal(all=True):
                print(signal)
        #   Store outcomes and associated parameters
        return self.symbol
