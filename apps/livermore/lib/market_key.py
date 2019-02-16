from livermore import *

import olympus.equities_us.data.price as price

class Chart():
    # Manage charts associated with the Livermore Market Key.
    # For an example of the original Livermore paper charts, see 
    # Jesse L. Livermore, "How to Trade in Stocks, First Edition, pp. 102-133

    def __init__(self,user=USER,**kwargs):
        #super(Quote,self).__init__(user,'quote',**kwargs)
        pass

    def chart(self,symbol=SYMBOL,**kwargs):
        # Given an equity symbol, will generate chart points based on the Livermore Market key
        # kwargs:
        # continuation: Threshold for CONTINUATION
        # reversal: Threshold for reversal
        # 
        # 
        # 
        pass

class Backtest(Chart):

    def __init__(self,user=USER,**kwargs):
        #super(Quote,self).__init__(user,'quote',**kwargs)
        pass

    def backtest(self,symbol=SYMBOL,**kwargs):
        # 
        # 
        # 
        pass

