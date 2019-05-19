import olympus.equities_us.data.price as price

from richard import *

class PositionSizing(object):

    def __init__(self):
        pass

class Chart(object):

    def __init__(self,**kwargs):
        self.meta = { 'Date': dt.now().strftime('%Y-%m-%d %H:%M:%S.%f') }
        self.dates = []
        self.signals = { BUY: [], SELL: [] }
        self.watch = { BUY: [], SELL: [] }
    
    def add_date(self,date,price,adjusted_price,trend=None,warning=None):
        date = Date(date,price,adjusted_price,trend,warning)
        self.dates.append(date)
    
class Calculate(object):

    def __init__(self,symbol=SYMBOL,user=USER,**kwargs):
        self.user = user
        self.regen = kwargs.get('regen',False)
        self.symbol = symbol
        symbol_object = symbols.Read()
        self.symbol_record = symbol_object.get_symbol(symbol)
        if self.symbol_record is None:
            raise Exception('Symbol ' + symbol + ' not located.')
        self.price_object = price.Quote()

    def chartpoints(self,**kwargs):
        pass
