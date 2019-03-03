import json

from datetime import datetime as dt
from operator import itemgetter

import olympus.equities_us.data.price as price
import olympus.equities_us.data.symbols as symbols

from larry import *

class ChartDate(object):

    def __init__(self,date,price,trend):
        self.date = date
        self.price = price
        self.trend = trend
        self.warning = None

class Chart(object):

    def __init__(self,start_date,end_date,**kwargs):
        self.meta = { 'Date': dt.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'Start Date': start_date, 'End Date': end_date }
        self.dates = []
        self.pivots = { 'Upward': [], 'Downward': [], 'Rally': [], 'Reaction': [] }
        self.signals = { 'Buy': [], 'Sell': [] }
    
    def active_warning(self):
        entry = self.last_entry()
        if entry is not None and entry.warning is not None:
            return entry.warning
        return None
    
    def add_date(self,date,price,trend=None,warning=None):
        date = ChartDate(date,price,trend,warning)
        self.dates.append(date)
    
    def add_meta(self,key,data):
        self.meta[key] = data
    
    def empty(self):
        if self.dates:
            return False
        return True

    def last_entry(self):
        if self.dates:
            return self.dates[-1]
        return None

    def last_pivot(self,type):
        if self.pivots[type]:
            return self.pivots[type][-1]
        return None

    def last_price(self):
        if self.dates:
            return self.last_entry().price
        return None

    def last_trend(self):
        if self.dates:
            return self.dates[-1].trend
        return None

class Datapoint(object):

    def __init__(self,datapoint,thresholds,**kwargs):
        self.close = float(datapoint['close'])
        self.high = float(datapoint['high'])
        self.low = float(datapoint['low'])
        self.pivot = None
        self.signal = None
        matching_scheme = None
        minimum = 0.0
        for scheme in sorted(thresholds, key=itemgetter('Continuation')) :
            if self.close > minimum and ('Maximum' not in scheme or self.close <= float(scheme['Maximum'])):
                matching_scheme = scheme
                break
            minimum = scheme['Maximum']
        if matching_scheme is None:
            self.continuation = CONTINUATION
            self.reversal = REVERSAL
            self.short_distance = SHORT_DISTANCE
        else:
            self.continuation = float(matching_scheme['Continuation'])
            self.reversal = float(matching_scheme['Reversal'])
            self.short_distance = float(matching_scheme['Short Distance'])

    def chart(self,chart,**kwargs):
        if chart.last_trend() == UPWARD_TREND or chart.last_trend() == DOWNWARD_TREND:
            self._trend(chart)
        elif chart.last_trend() == NATURAL_RALLY or chart.last_trend() == NATURAL_REACTION:
            self._countertrend(chart)
        elif chart.last_trend() == SECONDARY_RALLY or chart.last_trend() == SECONDARY_REACTION:
            self._secondary(chart)

    def _trend(self,chart):
        price = None
        trend = None
        if chart.last_trend() == UPWARD_TREND:
            comp = _gt
            comp_reverse = _lt
            level = self.high
        else: # DOWNWARD_TREND
            comp = _lt
            comp_reverse = _gt
            level = self.low
        if comp(level,chart.last_price()):
            # Rule 1; Rule 2
            trend = chart.last_trend()
            price = level
            warning = chart.active_warning()
            if warning is not None and warning == chart.last_trend():
                # Rule 10b; Rule 10c
                if comp_reverse(

    def _countertrend(self,chart):
        pass

    def _secondary_trend(self,chart):
        pass

    def _gt(self,val1,val2):
        return (val1 > val2)

    def _lt(self,val1,val2):
        return (val1 < val2)

class Calculate(object):
    # Generate summary associated with the Livermore Market Key.
    # For an example of the original Livermore paper charts, see 
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition, pp. 102-133
    # Numbered rules referred to below are from Chapter 10, "Explanatory Rules", pp. 91-101

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
        # Given an equity symbol, will generate chart points based on the Livermore Market key
        thresholds = kwargs.get('thresholds',THRESHOLDS)
        start_date = kwargs.get('start_date',START_CHART.strftime('%Y-%m-%d'))
        end_date = kwargs.get('end_date',END_CHART.strftime('%Y-%m-%d'))

        # Create storage
        self.chart = Chart(start_date,end_date) 
        self.chart.add_meta('Thresholds',thresholds)

		# Get symbol/price data
        daily_price_series = self.price_object.daily(self.symbol,regen=self.regen,start_date=start_date,end_date=end_date)
        if daily_price_series is None:
            raise Exception('Daily price series for ' + self.symbol + ' not located for date range.')

        # Evaluate
        for date, price in daily_price_series.items():
            datapoint = Datapoint(price,thresholds)
            if self.chart.empty():
                # Starting price (use closing price, but only to INITIATE records)
                self.chart.add_date(date,datapoint.close)
            elif self.chart.last_trend() is None:
                # Starting trend
                last_entry = self.chart.last_entry()
                if datapoint.close > last_entry.price:
                    self.chart.add_date(date,datapoint.high,UPWARD_TREND)
                elif datapoint.close < last_entry.price:
                    self.chart.add_date(date,datapoint.low,DOWNWARD_TREND)
            else:
                datapoint.chart(self.chart)
        return self.chart

    def _add_pivot(self,pivots,date,price,type,rule=None):
        pivot = {}
        pivot['Date'] = date
        pivot['Price'] = price
        signal['Rule'] = rule
        pivots[type].append(pivot)
        return pivots

    def _add_signal(self,signals,date,price,type,memo,rule=None):
        signal = {}
        signal['Date'] = date
        signal['Price'] = price
        signal['Memo'] = memo
        signal['Rule'] = rule
        signals[type].append(signal)
        return signals

class Trade(object):
    # Trading the Livermore Market Key.

    def __init__(self,symbol=SYMBOL,user=USER,**kwargs):
        self.symbol = symbol

    def simulate(self,**kwargs):
        purchase_size = kwargs.get('purchase_size',PURCHASE_SIZE)
