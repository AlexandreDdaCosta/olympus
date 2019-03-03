import json

from datetime import datetime as dt
from operator import itemgetter

import olympus.equities_us.data.price as price
import olympus.equities_us.data.symbols as symbols

from larry import *

class Date(object):

    def __init__(self,date,price,trend):
        self.date = date
        self.price = price
        self.trend = trend
        self.warning = None

    def reset_warning(self):
        self.warning = None

class Pivot(object):

    def __init__(self,date,price,type,rule=None):
        self.date = date
        self.price = price
        self.type = type
        self.rule = rule

class Signal(object):

    def __init__(self,date,price,type,memo,rule=None)
        self.date = date
        self.price = price
        self.type = type
        self.memo = memo
        self.rule = rule

class Chart(object):

    def __init__(self,start_date,end_date,**kwargs):
        self.meta = { 'Date': dt.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'Start Date': start_date, 'End Date': end_date }
        self.dates = []
        self.pivots = { UPWARD_TREND: [], DOWNWARD_TREND: [], NATURAL_RALLY: [], NATURAL_REACTION: [] }
        self.signals = { BUY: [], SELL: [] }
    
    def active_warning(self):
        entry = self.last_entry()
        if entry is not None and entry.warning is not None:
            return entry.warning
        return None
    
    def add_date(self,date,price,trend=None,warning=None):
        date = Date(date,price,trend,warning)
        self.dates.append(date)
    
    def add_meta(self,key,data):
        self.meta[key] = data
    
    def buy_signal(self,date,price,memo,rule=None):
        return self._add_signal(date,price,BUY,memo,rule):

    def cancel_warning(self):
        if self.dates:
            self.dates[-1].reset_warning()
    
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

    def sell_signal(self,date,price,memo,rule=None):
        return self._add_signal(date,price,SELL,memo,rule):

    def _add_signal(self,date,price,type,memo,rule):
        signal = Signal(date,price,type,trend,rule)
        self.signals[type].append(date)
    
class Datapoint(object):

    def __init__(self,date,datapoint,thresholds,**kwargs):
        self.date = date
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
        # Three major categories of price trend, each with two trends of similar logic but with logical comparisons reversed
        if chart.last_trend() == UPWARD_TREND or chart.last_trend() == DOWNWARD_TREND:
            trend = self._trend
        elif chart.last_trend() == NATURAL_RALLY or chart.last_trend() == NATURAL_REACTION:
            trend = self._countertrend
        elif chart.last_trend() == SECONDARY_RALLY or chart.last_trend() == SECONDARY_REACTION:
            trend = self._secondary
        price, trend, warning = trend(chart)
        if trend is not None:
            chart.add_date(self.date,price,trend,warning)

    def _trend(self,chart):
        price, trend, warning = (None, None, None)
        # Defaults are for trend continuation, "reversal" for trend reversal or opposite action
        if chart.last_trend() == UPWARD_TREND:
            comparison = _gt
            reversal_comparison = _lt
            level = self.high
            reversal_level = self.low
            memo = 'Reaction to Upward'
            rule = '10a'
            reversal_rule = '10b'
            signal = chart.buy_signal
            reversal_signal = chart.sell_signal
            continuing = _add
            reversing = _subtract
            countertrend = DOWNWARD_TREND
            natural_countertrend = NATURAL_REACTION
        else: # DOWNWARD_TREND
            comparison = _lt
            reversal_comparison = _gt
            level = self.low
            reversal_level = self.high
            memo = 'Rally to Downward'
            rule = '10c'
            reversal_rule = '10d'
            signal = chart.sell_signal
            reversal_signal = chart.buy_signal
            continuing = _subtract
            reversing = _add
            countertrend = UPWARD_TREND
            natural_countertrend = NATURAL_RALLY
        reversal_memo = memo + ' Failure'
        if comparison(level,chart.last_price()):
            # Rule 1; Rule 2
            price = level
            trend = chart.last_trend()
            if chart.active_warning() is not None and chart.active_warning() == chart.last_trend():
                # Rule 10b; Rule 10c
                if reverse_comparison(price,continuing(chart.last_pivot(chart.last_trend()),self.continuation)):
                    warning = chart.last_trend()
                else:
                    signal(self.date,continuing(chart.last_pivot(chart.last_trend()),self.continuation),memo,rule)
        else:
            price = reversal_level
            if chart.active_warning() is not None and chart.active_warning() == chart.last_trend() and reverse_comparison(price,reversing(chart.last_pivot(chart.last_trend()),self.continuation)):
                chart.cancel_warning()
                reversal_signal(self.date,reversing(chart.last_pivot(chart.last_trend()),self.continuation),reversal_memo,reversal_rule)
            if chart.last_pivot(chart.last_trend()) is not None and :

            elif price :

            #ALEX
        
    def _countertrend(self,chart):
        pass

    def _secondary_trend(self,chart):
        pass

    def _add(self,val1,val2):
        return (val1 + val2)

    def _subtract(self,val1,val2):
        return (val1 - val2)

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
            datapoint = Datapoint(date,price,thresholds)
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

class Trade(object):
    # Trading the Livermore Market Key.

    def __init__(self,symbol=SYMBOL,user=USER,**kwargs):
        self.symbol = symbol

    def simulate(self,**kwargs):
        purchase_size = kwargs.get('purchase_size',PURCHASE_SIZE)
