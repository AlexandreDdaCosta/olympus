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
    
    def add_pivot(self,date,price,type,rule=None):
        pivot = Pivot(date,price,type,rule)
        self.pivots[type].append(date)
    
    def buy_signal(self,date,price,memo,rule=None):
        return self._add_signal(date,price,BUY,memo,rule):

    def cancel_warning(self):
        if self.dates:
            self.dates[-1].reset_warning()
    
    def empty(self):
        if self.dates:
            return False
        return True

    def last_date(self):
        if self.dates:
            return self.last_entry().date
        return None

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
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition
    # Numbered rules referred to below are from Chapter 10, "Explanatory Rules", pp. 91-101

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
        # Defaults are for trend continuation, "opposite" for opposing trend or action
        if chart.last_trend() == UPWARD_TREND:
            comparison = self._gt
            opposite_comparison = self._lt
            level = self.high
            opposite_level = self.low
            memo = 'Reaction to Upward'
            operator = self._add
            opposite_operator = self._subtract
            rule = '10a'
            opposite_rule = '10b'
            signal = chart.buy_signal
            opposite_signal = chart.sell_signal
            countertrend = DOWNWARD_TREND
            countertrend_memo = 'Upward to Downward'
            natural_countertrend = NATURAL_REACTION
            natural_countertrend_rule = '6a'
            reversal_comparison = self._lteq
        else: # DOWNWARD_TREND
            comparison = self._lt
            opposite_comparison = self._gt
            level = self.low
            opposite_level = self.high
            memo = 'Rally to Downward'
            operator = self._subtract
            opposite_operator = self._add
            rule = '10c'
            opposite_rule = '10d'
            signal = chart.sell_signal
            opposite_signal = chart.buy_signal
            countertrend = UPWARD_TREND
            countertrend_memo = 'Downward to Upward'
            natural_countertrend = NATURAL_RALLY
            natural_countertrend_rule = '6c'
            reversal_comparison = self._gteq
        opposite_memo = memo + ' Failure'
        if comparison(level,chart.last_price()):
            # Rule 1/2
            price = level
            trend = chart.last_trend()
            if chart.active_warning() is not None and chart.active_warning() == chart.last_trend():
                # Rule 10.(a)/10.(c)
                if opposite_comparison(price,operator(chart.last_pivot(chart.last_trend()),self.continuation)):
                    warning = chart.last_trend()
                else:
                    signal(self.date,operator(chart.last_pivot(chart.last_trend()),self.continuation),memo,rule)
        else:
            price = opposite_level
            if (chart.active_warning() is not None and 
                chart.active_warning() == chart.last_trend() and 
                opposite_comparison(price,opposite_operator(chart.last_pivot(chart.last_trend()),self.continuation)):
                # Rule 10.(b)/10.(d)
                chart.cancel_warning()
                opposite_signal(self.date,opposite_operator(chart.last_pivot(chart.last_trend()),self.continuation),opposite_memo,opposite_rule)
            if chart.last_pivot(countertrend) is not None and opposite_comparison(price,chart.last_pivot(countertrend).price):
                # Added rule specifies what happens if a trend reverses past the nearest pivot of the opposite trend
                trend = countertrend
                opposite_signal(self.date,chart.last_pivot(countertrend).price,countertrend_memo)
            elif reversal_comparison(price,opposite_operator(chart.last_price(),self.reversal)):
                # Rule 6.(a)/6.(c)
                trend = natural_countertrend
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),natural_countertrend_rule)
        return price, trend, warning

    def _countertrend(self,chart):
        price, trend, warning = (None, None, None)
        if chart.last_trend() == NATURAL_RALLY:
            comparison = self._gt
            opposite_comparison = self._lt
            comparison_eq = self._gteq
            opposite_comparison_eq = self._lteq
            level = self.high
            opposite_level = self.low
            operator = self._subtract
            opposite_operator = self._add
            signal = chart.buy_signal
            opposite_signal = chart.sell_signal
            memo = 'Rally to Upward'
            rule = '6f'
            memo_continue = 'Rally Continuation to Upward'
            rule_continue = '5a'
            memo_warning = 'Rally to Upward Failure'
            rule_warning = '10e'
            rule_followthrough = '6d'
            rule_reversal = '6h'
            continue_trend = UPWARD_TREND
            reversal_trend = DOWNWARD_TREND
            opposing_trend = NATURAL_REACTION
            secondary_trend = SECONDARY_REACTION
        else: # NATURAL_REACTION
            comparison = self._lt
            opposite_comparison = self._gt
            comparison_eq = self._lteq
            opposite_comparison_eq = self._gteq
            level = self.low
            opposite_level = self.high
            operator = self._add
            opposite_operator = self._subtract
            signal = chart.sell_signal
            opposite_signal = chart.buy_signal
            memo = 'Reaction to Downward'
            rule = '6e'
            memo_continue = 'Reaction Continuation to Downward'
            rule_continue = '5b'
            memo_warning = 'Reaction to Downward Failure'
            rule_warning = '10f'
            rule_followthrough = '6b'
            rule_reversal = '6g'
            continue_trend = DOWNWARD_TREND
            reversal_trend = UPWARD_TREND
            opposing_trend = NATURAL_RALLY
            secondary_trend = SECONDARY_RALLY
        if comparison(level,chart.last_price()):
            price = level
            if (chart.last_pivot(continue_trend) is not None and 
                comparison_eq(price,operator(chart.last_pivot(continue_trend).price,self.short_distance)) and 
                opposite_comparison(price,chart.last_pivot(continue_trend).price):
                # Rule 10.(e)/10.(f)
                warning = continue_trend
            if chart.last_pivot(continue_trend) is not None and comparison_eq(price,chart.last_pivot(continue_trend).price):
                # Rule 6.(e)/6.(f)
                trend = continue_trend
                signal(self.date,chart.last_pivot(continue_trend).price,memo,rule)
            elif (chart.last_pivot(chart.last_trend()) is not None and 
                comparison_eq(price,opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation))):
                # Rule 5.(a)/5.(b)
                trend = continue_trend
                signal(self.date,opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation),memo_continue,rule_continue)
            else:
                # Rule 6.(a)/6.(c)
                trend = chart.last_trend()
        else:
            price = opposite_level
            if (chart.active_warning() is not None and 
                chart.active_warning() == continue_trend and 
                opposite_comparison_eq(price,operator(chart.last_pivot(continue_trend).price,self.continuation)):
                    # Rule 10.(e)/10.(f)
                    chart.cancel_warning()
                    opposite_signal(self.date,operator(chart.last_pivot(continue_trend).price,self.continuation),memo_warning,rule_warning)
            if chart.last_pivot(reversal_trend) is not None and opposite_comparison_eq(price,chart.last_pivot(reversal_trend).price):
                trend = reversal_trend
                if comparison(opposite_level,operator(chart.last_pivot(reversal_trend).price,self.continuation)):
                    # Rule 10.(e)/10.(f)
                    warning = reversal_trend
                # Rule 6.(b)/6.(d)
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),rule_followthrough)
            elif opposite_comparison(price,operator(chart.last_price(),self.reversal)):
                if chart.last_pivot(opposing_trend) is not None and comparison(price,chart.last_pivot(opposing_trend).price):
                    # Rule 6.(g)/6.(h)
                    trend = secondary_trend
                else:
                    trend = opposing_trend
                    chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),rule_reversal)
        return price, trend, warning

    def _secondary_trend(self,chart):
        price, trend = (None, None)
        if chart.last_trend() == SECONDARY_RALLY:
            comparison = self._gt
            opposite_comparison = self._lt
            opposite_comparison_eq = self._lteq
            level = self.high
            opposite_level = self.low
            signal = chart.buy_signal
            opposite_signal = chart.sell_signal
            memo = 'Secondary Rally to Upward'
            rule = '6d'
            memo_reversal = 'Secondary Rally to Downward'
            rule_reversal = '6h'
            continue_trend = UPWARD_TREND
            reversal_trend = DOWNWARD_TREND
            confirmation_trend = NATURAL_RALLY
            countertrend = NATURAL_REACTION
        else: # SECONDARY_REACTION
            comparison = self._lt
            opposite_comparison = self._gt
            opposite_comparison_eq = self._gteq
            level = self.low
            opposite_level = self.high
            signal = chart.sell_signal
            opposite_signal = chart.buy_signal
            memo = 'Secondary Reaction to Downward'
            rule = '6b'
            memo_reversal = 'Secondary Reaction to Upward'
            rule_reversal = '6g'
            continue_trend = DOWNWARD_TREND
            reversal_trend = UPWARD_TREND
            confirmation_trend = NATURAL_REACTION
            countertrend = NATURAL_RALLY
        if comparison(level,chart.last_price()):
            price = level
            if chart.last_pivot(continue_trend) is not None and comparison(price,chart.last_pivot(continue_trend).price):
                # Rule 6.(b)/6.(d)
                trend = continue_trend
                signal(self.date,last_pivot(continue_trend).price,memo,rule)
            elif comparison(price,last_pivot(confirmation_trend).price):
                # Rule 6.(g)/6.(h)
                trend = confirmation_trend
            else:
                # Rule 6.(g)/6.(h)
                trend = chart.last_trend()
        elif opposite_comparison_eq(opposite_level,chart.last_price()):
            price = opposite_level
            if chart.last_pivot(reversal_trend) is not None and opposite_comparison(price,chart.last_pivot(reversal_trend).price):
                # Rule 6.(b)/6.(d)
                trend = reversal_trend
                opposite_signal(self.date,last_pivot(reversal_trend).price,memo_reversal,rule_reversal)
            elif chart.last_pivot(countertrend) is not None and opposite_comparison_eq(price,chart.last_pivot(countertrend).price):
                trend = countertrend
        return price, trend, None

    def _add(self,val1,val2):
        return (val1 + val2)

    def _subtract(self,val1,val2):
        eturn (val1 - val2)

    def _gt(self,val1,val2):
        return (val1 > val2)

    def _gteq(self,val1,val2):
        return (val1 >= val2)

    def _lteq(self,val1,val2):
        return (val1 <= val2)

class Calculate(object):
    # Generate summary associated with the Livermore Market Key.
    # For an example of the original Livermore paper charts, see 
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition, pp. 102-133

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