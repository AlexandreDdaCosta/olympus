import json

from datetime import datetime as dt
from operator import itemgetter

import olympus.equities_us.data.price as price
import olympus.equities_us.data.symbols as symbols

from larry import *
from olympus.equities_us import BUY, SELL, SYMBOL

class Warning(object):

    def __init__(self,trend,pivot,subtype):
        self.trend = trend
        self.pivot = pivot
        self.subtype = subtype

    def __repr__(self):
        return "Warning(trend=%r,pivot=%r,subtype=%r)" % (self.trend,self.pivot,self.subtype)

class Date(object):

    def __init__(self,date,price,adjusted_price,trend,warning=None,pivot_warning=None,counterpivot_warning=None):
        self.date = date
        self.price = price
        self.adjusted_price = adjusted_price
        self.trend = trend
        self.warning = warning
        self.pivot_warning = pivot_warning
        self.counterpivot_warning = counterpivot_warning

    def __repr__(self):
        if self.warning is not None:
            return "Date(date=%r,price=%.2f,adjusted_price=%.2f,trend=%r,warning=%r)" % (self.date,self.price,self.adjusted_price,self.trend,self.warning)
        return "Date(date=%r,price=%.2f,adjusted_price=%.2f,trend=%r)" % (self.date,self.price,self.adjusted_price,self.trend)

    def set_counterpivot_warning(self,trend,pivot,subtype):
        warning = Warning(trend,pivot,subtype)
        self.counterpivot_warning = warning

    def set_pivot_warning(self,trend,pivot,subtype):
        warning = Warning(trend,pivot,subtype)
        self.pivot_warning = warning

    def reset_counterpivot_warning(self):
        self.counterpivot_warning = None

    def reset_pivot_warning(self):
        self.pivot_warning = None

    def reset_warning(self):
        self.warning = None

class Pivot(object):

    def __init__(self,date,price,trend,rule,adjusted_price):
        self.date = date
        self.price = price
        self.trend = trend
        self.rule = rule
        self.adjusted_price = adjusted_price

    def __repr__(self):
        return "Pivot(date=%r,price=%.2f,trend=%r,rule=%r,adjusted_price=%.2f)" % (self.date,self.price,self.trend,self.rule,self.adjusted_price)

class Signal(object):

    def __init__(self,date,price,subtype,memo,rule):
        self.date = date
        self.price = price
        self.signal = subtype
        self.subtype = subtype
        self.memo = memo
        self.rule = rule

    def __repr__(self):
        return "Signal(date=%r,price=%.2f,type=%r,memo=%r,rule=%r)" % (self.date,self.price,self.subtype,self.memo,self.rule)

class Watch(object):

    def __init__(self,price,signal,rule):
        self.price = price
        self.signal = signal
        self.rule = rule

    def __repr__(self):
        return "Watch(price=%.2f,signal=%r,rule=%r)" % (self.price,self.signal,self.rule)

class Chart(object):

    def __init__(self,**kwargs):
        self.meta = { 'Date': dt.now().strftime('%Y-%m-%d %H:%M:%S.%f') }
        self.dates = []
        self.pivots = { UPWARD_TREND: [], DOWNWARD_TREND: [], NATURAL_RALLY: [], NATURAL_REACTION: [] }
        self.signals = { BUY: [], SELL: [] }
        self.watch = { BUY: [], SELL: [] }
    
    def active_warning(self):
        entry = self.last_entry()
        if entry is not None and entry.warning is not None:
            return entry.warning
        return None
    
    def add_watch(self,price,signal_type,rule):
        watch = Watch(price,signal_type,rule)
        self.watch[signal_type].append(watch)
    
    def add_date(self,date,price,adjusted_price,trend=None,warning=None):
        date = Date(date,price,adjusted_price,trend,warning)
        self.dates.append(date)
    
    def add_meta(self,key,data):
        self.meta[key] = data
    
    def add_pivot(self,date,price,trend,rule,adjusted_price):
        pivot = Pivot(date,price,trend,rule,adjusted_price)
        self.pivots[trend].append(pivot)
    
    def buy_watch(self):
        if self.watch[BUY]:
            return self.watch[BUY]
        return None

    def buy_signal(self,date,price,memo,rule=None):
        return self._add_signal(date,price,BUY,memo,rule)

    def cancel_watch(self):
        self.watch = { BUY: [], SELL: [] }
    
    def cancel_warning(self):
        if self.dates:
            self.dates[-1].reset_warning()
    
    def empty(self):
        if self.dates:
            return False
        return True

    def has_pivot(self,trend):
        if self.pivots[trend]:
            return True
        return False
    
    def has_signal(self,subtype):
        if self.signals[subtype]:
            return True
        return False
    
    def last_adjusted_price(self):
        if self.dates:
            return self.last_entry().adjusted_price
        return None

    def last_buy_signal(self,quantity=1,**kwargs):
        return self._last_signal(BUY,quantity,**kwargs)

    def last_date(self):
        if self.dates:
            return self.last_entry().date
        return None

    def last_downward_pivot(self,quantity=1,**kwargs):
        return self._last_pivot(DOWNWARD_TREND,quantity,**kwargs)

    def last_entry(self):
        if self.dates:
            return self.dates[-1]
        return None

    def last_pivot(self,trend):
        if self.pivots[trend]:
            return self.pivots[trend][-1]
        return None

    def last_pivots(self):
        last_pivots = {}
        for trend in [UPWARD_TREND, DOWNWARD_TREND, NATURAL_RALLY, NATURAL_REACTION]:
            if self.pivots[trend]:
                last_pivots[trend] = self.pivots[trend][-1]
        return last_pivots

    def last_price(self):
        if self.dates:
            return self.last_entry().price
        return None

    def last_rally_pivot(self,quantity=1,**kwargs):
        return self._last_pivot(NATURAL_RALLY,quantity,**kwargs)

    def last_reaction_pivot(self,quantity=1,**kwargs):
        return self._last_pivot(NATURAL_REACTION,quantity,**kwargs)

    def last_sell_signal(self,quantity=1,**kwargs):
        return self._last_signal(SELL,quantity,**kwargs)

    def last_trend(self):
        if self.dates:
            return self.dates[-1].trend
        return None

    def last_upward_pivot(self,quantity=1,**kwargs):
        return self._last_pivot(UPWARD_TREND,quantity,**kwargs)

    def sell_watch(self):
        if self.watch[SELL]:
            return self.watch[SELL]
        return None

    def sell_signal(self,date,price,memo,rule=None):
        return self._add_signal(date,price,SELL,memo,rule)

    def _add_signal(self,date,price,subtype,memo,rule):
        signal = Signal(date,price,subtype,memo,rule)
        self.signals[subtype].append(signal)

    def _last_pivot(self,trend,quantity,**kwargs):
        all = kwargs.get('all',False)
        if self.pivots[trend]:
            if all is True:
                return self.pivots[trend]
            else:
                return self.pivots[trend][-quantity:]
        return None

    def _last_signal(self,subtype,quantity,**kwargs):
        all = kwargs.get('all',False)
        if self.signals[subtype]:
            if all is True:
                return self.signals[subtype]
            else:
                return self.signals[subtype][-quantity:]
        return None

class DatapointVariables(object):

    def pivot(self,trend,chart,direction):
        if trend in UPWARD_TRENDS:
            self.comparison = self.gt
            self.comparison_eq = self.gteq
            self.opposite_comparison = self.lt
            self.opposite_comparison_eq = self.lteq
            self.signal = chart.buy_signal
            self.opposite_signal = chart.sell_signal
            self.operator = self.add
            self.opposite_operator = self.subtract
        else:
            self.comparison = self.lt
            self.comparison_eq = self.lteq
            self.opposite_comparison = self.gt
            self.opposite_comparison_eq = self.gteq
            self.signal = chart.sell_signal
            self.opposite_signal = chart.buy_signal
            self.operator = self.subtract
            self.opposite_operator = self.add
        if direction == 'trend':
            if trend in UPWARD_TRENDS:
                self.trend_pivots = chart.last_upward_pivot
                self.natural_pivots = chart.last_rally_pivot
                if trend == UPWARD_TREND:
                    self.breakout_rule = '14a'
                    self.reversal_continuation_rule = '14g'
                    self.reversal_short_distance_rule = '14m'
                elif trend == NATURAL_RALLY:
                    self.breakout_rule = '14b'
                    self.reversal_continuation_rule = '14h'
                    self.reversal_short_distance_rule = '14n'
                else: # SECONDARY_RALLY
                    self.breakout_rule = '14c'
                    self.reversal_continuation_rule = '14i'
                    self.reversal_short_distance_rule = '14o'
            else:
                self.trend_pivots = chart.last_downward_pivot
                self.natural_pivots = chart.last_reaction_pivot
                if trend == DOWNWARD_TREND:
                    self.breakout_rule = '14d'
                    self.reversal_continuation_rule = '14j'
                    self.reversal_short_distance_rule = '14p'
                elif trend == NATURAL_REACTION:
                    self.breakout_rule = '14e'
                    self.reversal_continuation_rule = '14k'
                    self.reversal_short_distance_rule = '16q'
                else: # SECONDARY_REACTION
                    self.breakout_rule = '14f'
                    self.reversal_continuation_rule = '14l'
                    self.reversal_short_distance_rule = '14r'
            self.breakout_memo = trend + ' pivot breakout'
            self.reversal_continuation_memo = trend = ' continuation failure'
            self.reversal_memo = trend + ' pivot reversal'
            self.reversal_short_distance_memo = trend = ' short distance failure'
        elif direction == 'countertrend':
            if trend in UPWARD_TRENDS:
                self.trend_pivots = chart.last_downward_pivot
                self.natural_pivots = chart.last_reaction_pivot
                if trend == UPWARD_TREND:
                    self.breakout_rule = '15a'
                    self.reversal_continuation_rule = '15g'
                    self.reversal_short_distance_rule = '15m'
                elif trend == NATURAL_RALLY:
                    self.breakout_rule = '15b'
                    self.reversal_continuation_rule = '15h'
                    self.reversal_short_distance_rule = '15n'
                else: # SECONDARY_RALLY
                    self.breakout_rule = '15c'
                    self.reversal_continuation_rule = '15i'
                    self.reversal_short_distance_rule = '15o'
            else:
                self.trend_pivots = chart.last_upward_pivot
                self.natural_pivots = chart.last_rally_pivot
                if trend == DOWNWARD_TREND:
                    self.breakout_rule = '15d'
                    self.reversal_continuation_rule = '15j'
                    self.reversal_short_distance_rule = '15p'
                elif trend == NATURAL_REACTION:
                    self.breakout_rule = '15e'
                    self.reversal_continuation_rule = '15k'
                    self.reversal_short_distance_rule = '15q'
                else: # SECONDARY_REACTION
                    self.breakout_rule = '15f'
                    self.reversal_continuation_rule = '15l'
                    self.reversal_short_distance_rule = '15r'
            self.breakout_memo = trend + ' counterpivot breakout'
            self.reversal_continuation_memo = trend + ' counter continuation failure'
            self.reversal_memo = trend + ' counterpivot reversal'
            self.reversal_short_distance_memo = trend + ' counter short distance failure'
        else:
            raise Exception('Logic error in trend type for datapoint variable assignment')

    def trend(self,trend,chart):
        # Defaults are for trend continuation, "opposite" for opposing trend or action
        if trend == UPWARD_TREND or trend == DOWNWARD_TREND:
            if trend == UPWARD_TREND:
                self.comparison = self.gt
                self.opposite_comparison = self.lt
                self.reversal_comparison = self.lteq
                self.countertrend = DOWNWARD_TREND
                self.natural_countertrend = NATURAL_REACTION
                self.natural_trend = NATURAL_RALLY
                self.operator = self.add
                self.opposite_operator = self.subtract
                self.signal = chart.buy_signal
                self.signal_type = BUY
                self.opposite_signal = chart.sell_signal
                self.opposite_signal_type = SELL
                self.rule = '10a'
                self.countertrend_rule = '12a'
                self.natural_countertrend_rule = '6a'
                self.natural_rule = '10g'
                self.natural_trend_rule = '10h'
                self.opposite_rule = '10b'
                self.memo = 'Reaction to Upward'
                self.natural_memo = 'Rally to Upward'
                self.countertrend_memo = 'Upward to Downward'
            elif trend == DOWNWARD_TREND:
                self.comparison = self.lt
                self.opposite_comparison = self.gt
                self.reversal_comparison = self.gteq
                self.countertrend = UPWARD_TREND
                self.natural_countertrend = NATURAL_RALLY
                self.natural_trend = NATURAL_REACTION
                self.operator = self.subtract
                self.opposite_operator = self.add
                self.signal = chart.sell_signal
                self.signal_type = SELL
                self.opposite_signal = chart.buy_signal
                self.opposite_signal_type = BUY
                self.rule = '10c'
                self.countertrend_rule = '12b'
                self.natural_countertrend_rule = '6c'
                self.natural_rule = '10i'
                self.natural_trend_rule = '10j'
                self.opposite_rule = '10d'
                self.memo = 'Rally to Downward'
                self.natural_memo = 'Reaction to Downward'
                self.countertrend_memo = 'Downward to Upward'
            self.opposite_memo = self.memo + ' Failure'
            self.natural_trend_memo = self.natural_memo + ' Failure'
        elif trend == NATURAL_RALLY:
            self.comparison = self.gt
            self.comparison_eq = self.gteq
            self.opposite_comparison = self.lt
            self.opposite_comparison_eq = self.lteq
            self.continue_trend = UPWARD_TREND
            self.opposing_trend = NATURAL_REACTION
            self.reversal_trend = DOWNWARD_TREND
            self.secondary_trend = SECONDARY_REACTION
            self.operator = self.subtract
            self.opposite_operator = self.add
            self.signal = chart.buy_signal
            self.signal_type = BUY
            self.opposite_signal = chart.sell_signal
            self.opposite_signal_type = SELL
            self.rule = '6f'
            self.rule_continue = '5a'
            self.rule_followthrough = '6d'
            self.rule_pivot = '4d'
            self.rule_pivot_secondary = '13b'
            self.rule_warning = '10e'
            self.memo = 'Rally to Upward'
            self.memo_continue = 'Rally Continuation to Upward'
            self.memo_warning = 'Rally to Upward Failure'
        elif trend == NATURAL_REACTION:
            self.comparison = self.lt
            self.comparison_eq = self.lteq
            self.opposite_comparison = self.gt
            self.opposite_comparison_eq = self.gteq
            self.continue_trend = DOWNWARD_TREND
            self.opposing_trend = NATURAL_RALLY
            self.reversal_trend = UPWARD_TREND
            self.secondary_trend = SECONDARY_RALLY
            self.operator = self.add
            self.opposite_operator = self.subtract
            self.signal = chart.sell_signal
            self.signal_type = SELL
            self.opposite_signal = chart.buy_signal
            self.opposite_signal_type = SELL
            self.rule = '6e'
            self.rule_continue = '5b'
            self.rule_followthrough = '6b'
            self.rule_pivot = '4b'
            self.rule_pivot_secondary = '13a'
            self.rule_warning = '10f'
            self.memo = 'Reaction to Downward'
            self.memo_continue = 'Reaction Continuation to Downward'
            self.memo_warning = 'Reaction to Downward Failure'
        elif trend == SECONDARY_RALLY:
            self.comparison = self.gt
            self.opposite_comparison = self.lt
            self.opposite_comparison_eq = self.lteq
            self.confirmation_trend = NATURAL_RALLY
            self.continue_trend = UPWARD_TREND
            self.countertrend = NATURAL_REACTION
            self.reversal_trend = DOWNWARD_TREND
            self.signal = chart.buy_signal
            self.signal_type = BUY
            self.opposite_signal = chart.sell_signal
            self.opposite_signal_type = SELL
            self.rule = '6d'
            self.rule_pivot = '13d'
            self.rule_reversal = '6h'
            self.memo = 'Secondary Rally to Upward'
            self.memo_reversal = 'Secondary Rally to Downward'
        elif trend == SECONDARY_REACTION:
            self.comparison = self.lt
            self.opposite_comparison = self.gt
            self.opposite_comparison_eq = self.gteq
            self.confirmation_trend = NATURAL_REACTION
            self.continue_trend = DOWNWARD_TREND
            self.countertrend = NATURAL_RALLY
            self.reversal_trend = UPWARD_TREND
            self.signal = chart.sell_signal
            self.signal_type = SELL
            self.opposite_signal = chart.buy_signal
            self.opposite_signal_type = BUY
            self.rule = '6b'
            self.rule_pivot = '13c'
            self.rule_reversal = '6g'
            self.memo = 'Secondary Reaction to Downward'
            self.memo_reversal = 'Secondary Reaction to Upward'

    def add(self,val1,val2):
        return (val1 + val2)

    def subtract(self,val1,val2):
        return (val1 - val2)

    def gt(self,val1,val2):
        return (val1 > val2)

    def gteq(self,val1,val2):
        return (val1 >= val2)

    def lt(self,val1,val2):
        return (val1 < val2)

    def lteq(self,val1,val2):
        return (val1 <= val2)

class Datapoint(object):
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition
    # 
    # Numbered rules:
    # 
    # 1-10: See Chapter 10, "Explanatory Rules", pp. 91-101
    # 
    # Additional logic grouped with original rules:
    # 
    # 10. 
    #     10.g Whenever, after a Natural Rally has ended and new prices are being recorded in the 
    #          Upward Trend column, these new prices must extend three or more points above the last Pivotal Point 
    #          (with black lines underneath) if the Upward Trend is to be confirmed.
    #     10.h If the stock fails to do this, and on a reaction sells three or more points below the last Pivotal
    #          Point (recorded in the Upward Trend column with black lines drawn underneath), it would indicate that
    #          the Upward Trend in the stock is over.
    #     10.i Whenever, after a Natural Reaction has ended and new prices are being recorded in the 
    #          Downward Trend column, these new prices must extend three or more points below the last Pivotal Point 
    #          (with black lines underneath) if the Downward Trend is to be confirmed.
    #     10.j If the stock fails to do this, and on a rally sells three or more points above the last Pivotal
    #          Point (recorded in the Downward Trend column with black lines drawn underneath), it would indicate that
    #          the Downward Trend in the stock is over.
    # 
    # Additonal logic added as separate rules:
    # 
    # 11. 
    #     11.a To initialize empty records, use closing prices on the first two days to establish trend.
    #     11.b When recording the second day, a closing price higher than that of the first day will be recorded
    #          in the Upward Trend column. The low price will be entered in the Downward Trend column with a red 
    #          line drawn underneath to signify a pivotal point.
    #     11.c When recording the second day, a closing price lower than that of the first day will be recorded
    #          in the Downward Trend column. The high price will be entered in the Upward Trend column with a red 
    #          line drawn underneath to signify a pivotal point.
    # 12.
    #     12.a When recording in the Upward Trend column and a price is reached that is less than the last price
    #          recorded in the Downward Trend column (with black lines underneath), then that price should be entered 
    #          in black ink in the Downward Trend column.
    #     12.b When recording in the Downward Trend column and a price is reached that is greater than the last price
    #          recorded in the Upward Trend column (with black lines underneath), then that price should be entered 
    #          in black ink in the Upward Trend column.
    # 13.
    #     13.a Extend pivot rule 4.b for Natural Reaction to Secondary Rally
    #     13.b Extend pivot rule 4.a for Natural Rally to Secondary Reaction
    #     13.c Extend pivot rule 4.b for Secondary Reaction to Natural Rally or Upward Trend
    #     13.d Extend pivot rule 4.a for Secondary Rally to Natural Reaction or Downward Trend
    # 14. Rules in this section describe continuation, short distance, and reversal rules for
    #     historic pivots.
    #     10a/10c: Pivot breakout (continuation)
    #     10b/10d: Reversal from continuation failure
    #     10e/10f: Reversal from short distance
    #     14a. Apply 10a/10c to Upward Trend
    #     14b. Apply 10a/10c to Natural Rally
    #     14c. Apply 10a/10c to Secondary Rally
    #     14d. Apply 10a/10c to Downward Trend
    #     14e. Apply 10a/10c to Natural Reaction
    #     14f. Apply 10a/10c to Secondary Reaction
    #     14g. Apply 10b/10d to Upward Trend
    #     14h. Apply 10b/10d to Natural Rally
    #     14i. Apply 10b/10d to Secondary Rally
    #     14j. Apply 10b/10d to Downward Trend
    #     14k. Apply 10b/10d to Natural Reaction
    #     14l. Apply 10b/10d to Secondary Reaction
    #     14m. Apply 10e/10f to Upward Trend
    #     14n. Apply 10e/10f to Natural Rally
    #     14o. Apply 10e/10f to Secondary Rally
    #     14p. Apply 10e/10f to Downward Trend
    #     14q. Apply 10e/10f to Natural Reaction
    #     14r. Apply 10e/10f to Secondary Reaction
    # 15. Rules in this section describe continuation, short distance, and reversal rules for
    #     historic countertrend pivots. Countertrend pivots are those in a class opposite to
    #     the trend at breakout. An example would be breaking through a Downward Trend pivot
    #     during an Upward Trend.
    #     15a. Apply 10a/10c to Upward Trend
    #     15b. Apply 10a/10c to Natural Rally
    #     15c. Apply 10a/10c to Secondary Rally
    #     15d. Apply 10a/10c to Downward Trend
    #     15e. Apply 10a/10c to Natural Reaction
    #     15f. Apply 10a/10c to Secondary Reaction
    #     15g. Apply 10b/10d to Upward Trend
    #     15h. Apply 10b/10d to Natural Rally
    #     15i. Apply 10b/10d to Secondary Rally
    #     15j. Apply 10b/10d to Downward Trend
    #     15k. Apply 10b/10d to Natural Reaction
    #     15l. Apply 10b/10d to Secondary Reaction
    #     15m. Apply 10e/10f to Upward Trend
    #     15n. Apply 10e/10f to Natural Rally
    #     15o. Apply 10e/10f to Secondary Rally
    #     15p. Apply 10e/10f to Downward Trend
    #     15q. Apply 10e/10f to Natural Reaction
    #     15r. Apply 10e/10f to Secondary Reaction

    def __init__(self,date,datapoint,thresholds,**kwargs):
        self.date = date
        self.close = float(datapoint['close'])
        self.high = float(datapoint['high'])
        self.low = float(datapoint['low'])
        if 'adjusted close' in datapoint:
            self.adjusted_close = float(datapoint['adjusted close'])
            self.adjusted_high = float(datapoint['adjusted high'])
            self.adjusted_low = float(datapoint['adjusted low'])
        else:
            self.adjusted_close = self.close
            self.adjusted_high = self.high
            self.adjusted_low = self.low
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
        # Used to configure evaluation of historic pivots beyond the original market key specification
        oldest_pivot = kwargs.get('oldest_pivot',OLDEST_PIVOT)
        self.oldest_pivot = dt.strptime(self.date, "%Y-%m-%d") - relativedelta(years=oldest_pivot)
        self.pivot_logic = kwargs.get('pivot_logic',PIVOT_LOGIC_DEFAULT)
        if self.pivot_logic not in PIVOT_LOGIC:
            raise Exception('Invalid setting for pivot_logic')
        self.pivot_price_logic = kwargs.get('pivot_price_logic',PIVOT_PRICE_LOGIC_DEFAULT)
        if self.pivot_price_logic not in PIVOT_PRICE_LOGIC:
            raise Exception('Invalid setting for pivot_price_logic')

    def chart(self,chart):
        # Three major categories of price trend, each with two trends of similar logic but with logical comparisons reversed
        last_entry = chart.last_entry()
        last_trend = last_entry.trend
        if last_trend == UPWARD_TREND or last_trend == DOWNWARD_TREND:
            trend = self._trend
        elif last_trend == NATURAL_RALLY or last_trend == NATURAL_REACTION:
            trend = self._countertrend
        elif last_trend == SECONDARY_RALLY or last_trend == SECONDARY_REACTION:
            trend = self._secondary_trend
        price, adjusted_price, trend, warning = trend(chart)
        if trend is not None:
            chart.add_date(self.date,price,adjusted_price,trend,warning)
            self._added_signals(chart,last_entry)

    def watch(self,chart):
        chart.cancel_watch()
        price = chart.last_entry().price
        trend = chart.last_entry().trend
        warning = chart.active_warning()
        v = DatapointVariables()
        v.trend(trend,chart)
        if trend == UPWARD_TREND or trend == DOWNWARD_TREND:
            if warning is not None:
                pivot = chart.last_pivot(trend)
                if warning.trend == trend:
                    chart.add_watch(v.operator(pivot.price,self.continuation),v.signal_type,v.rule)
                    chart.add_watch(v.opposite_operator(pivot.price,self.continuation),v.opposite_signal_type,v.opposite_rule)
                elif warning.trend == v.natural_trend:
                    chart.add_watch(v.operator(pivot.price,self.continuation),v.signal_type,v.natural_rule)
                    chart.add_watch(v.opposite_operator(pivot.price,self.continuation),v.opposite_signal_type,v.natural_trend_rule)
            if chart.last_pivot(v.countertrend) is not None:
                chart.add_watch(chart.last_pivot(v.countertrend).price,v.opposite_signal_type,v.countertrend_rule)
        elif trend == NATURAL_RALLY or trend == NATURAL_REACTION:
            if warning is not None and warning.trend == v.continue_trend:
                chart.add_watch(v.operator(chart.last_pivot(v.continue_trend).price,self.continuation),v.opposite_signal_type,v.rule_warning)
            if chart.last_pivot(v.continue_trend) is not None:
                chart.add_watch(chart.last_pivot(v.continue_trend).price,v.signal_type,v.rule)
            if (chart.last_pivot(trend) is not None and 
                chart.last_pivot(v.opposing_trend) is not None and 
                v.opposite_comparison(chart.last_pivot(v.opposing_trend).price,chart.last_pivot(trend).price)):
                chart.add_watch(v.opposite_operator(chart.last_pivot(trend).price,self.continuation),v.signal_type,v.rule_continue)
        else: # SECONDARY_RALLY/SECONDARY_REACTION
            if chart.last_pivot(v.continue_trend) is not None:
                chart.add_watch(chart.last_pivot(v.continue_trend).price,v.signal_type,v.rule)
            if chart.last_pivot(v.reversal_trend) is not None:
                chart.add_watch(chart.last_pivot(v.reversal_trend).price,v.opposite_signal_type,v.rule_reversal)
        extended_pivots = self._nearest_extended_pivots(chart,price)
        for pivot_direction in ['upward','downward']:
            for pivot_trend in extended_pivots[pivot_direction]:
                if pivot_direction == 'upward':
                    if trend in UPWARD_TRENDS:
                        v.pivot(trend,chart,'trend')
                    else:
                        v.pivot(trend,chart,'countertrend')
                    warning = chart.last_entry().pivot_warning
                else:
                    if trend in DOWNWARD_TRENDS:
                        v.pivot(trend,chart,'trend')
                    else:
                        v.pivot(trend,chart,'countertrend')
                    warning = chart.last_entry().counterpivot_warning
                chart.add_watch(v.operator(extended_pivots[pivot_direction][pivot_trend].price,self.continuation),v.signal_type,v.breakout_rule)
                if warning is not None and warning.pivot is extended_pivots[pivot_direction][pivot_trend]:
                    if warning.subtype == 'short distance':
                        rule = v.reversal_short_distance_rule
                    else:
                        rule = v.reversal_continuation_rule
                    chart.add_watch(v.opposite_operator(extended_pivots[pivot_direction][pivot_trend].price,self.continuation),v.opposite_signal_type,rule)

    def _trend(self,chart):
        adjusted_price, price, trend, warning = (None, None, None, None)
        v = DatapointVariables()
        v.trend(chart.last_trend(),chart)
        if chart.last_trend() == UPWARD_TREND:
            level = self.high
            adjusted_level = self.adjusted_high
            opposite_level = self.low
            adjusted_opposite_level = self.adjusted_low
        else: # DOWNWARD_TREND
            level = self.low
            adjusted_level = self.adjusted_low
            opposite_level = self.high
            adjusted_opposite_level = self.adjusted_high
        if v.comparison(level,chart.last_price()):
            # Rule 1/2
            price = level
            adjusted_price = adjusted_level
            trend = chart.last_trend()
            if chart.active_warning() is not None:
                if chart.active_warning().trend == chart.last_trend():
                    # Rule 10.(a)/10.(c)
                    if v.opposite_comparison(price,v.operator(chart.last_pivot(chart.last_trend()).price,self.continuation)):
                        warning = Warning(chart.last_trend(),chart.last_pivot(chart.last_trend()),'continuation')
                    else:
                        v.signal(self.date,v.operator(chart.last_pivot(chart.last_trend()).price,self.continuation),v.memo,v.rule)
                elif chart.active_warning().trend == v.natural_trend:
                    # Rule 10.(g)/10.(i)
                    if v.opposite_comparison(price,v.operator(chart.last_pivot(chart.last_trend()).price,self.continuation)):
                        warning = Warning(v.natural_trend,chart.last_pivot(chart.last_trend()),'continuation')
                    else:
                        v.signal(self.date,v.operator(chart.last_pivot(chart.last_trend()).price,self.continuation),v.natural_memo,v.natural_rule)
                else:
                    raise Exception('Programming error in warning logic for trend')
        else:
            price = opposite_level
            adjusted_price = adjusted_opposite_level
            if (chart.active_warning() is not None and
                v.opposite_comparison(price,v.opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation))):
                if chart.active_warning().trend == chart.last_trend():
                    # Rule 10.(b)/10.(d)
                    chart.cancel_warning()
                    v.opposite_signal(self.date,v.opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation),v.opposite_memo,v.opposite_rule)
                elif chart.active_warning().trend == v.natural_trend:
                    # Rule 10.(h)/10.(j)
                    chart.cancel_warning()
                    v.opposite_signal(self.date,v.opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation),v.natural_trend_memo,v.natural_trend_rule)
                else:
                    raise Exception('Programming error in opposite warning logic for trend')
            if chart.last_pivot(v.countertrend) is not None and v.opposite_comparison(price,chart.last_pivot(v.countertrend).price):
                # Rule 12.(a)/12.(b)
                trend = v.countertrend
                v.opposite_signal(self.date,chart.last_pivot(v.countertrend).price,v.countertrend_memo,v.countertrend_rule)
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),v.countertrend_rule,chart.last_adjusted_price())
            elif v.reversal_comparison(price,v.opposite_operator(chart.last_price(),self.reversal)):
                # Rule 6.(a)/6.(c)
                trend = v.natural_countertrend
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),v.natural_countertrend_rule,chart.last_adjusted_price())
        return price, adjusted_price, trend, warning

    def _countertrend(self,chart):
        adjusted_price, price, trend, warning = (None, None, None, None)
        v = DatapointVariables()
        v.trend(chart.last_trend(),chart)
        if chart.last_trend() == NATURAL_RALLY:
            level = self.high
            adjusted_level = self.adjusted_high
            opposite_level = self.low
            adjusted_opposite_level = self.adjusted_low
        else: # NATURAL_REACTION
            level = self.low
            adjusted_level = self.adjusted_low
            opposite_level = self.high
            adjusted_opposite_level = self.adjusted_high
        if v.comparison(level,chart.last_price()):
            price = level
            adjusted_price = adjusted_level
            if (chart.last_pivot(v.continue_trend) is not None and 
                v.comparison_eq(price,v.operator(chart.last_pivot(v.continue_trend).price,self.short_distance)) and 
                v.opposite_comparison(price,chart.last_pivot(v.continue_trend).price)):
                # Rule 10.(e)/10.(f)
                warning = Warning(v.continue_trend,chart.last_pivot(v.continue_trend),'short distance')
            if chart.last_pivot(v.continue_trend) is not None and v.comparison_eq(price,chart.last_pivot(v.continue_trend).price):
                # Rule 6.(e)/6.(f)
                trend = v.continue_trend
                if v.opposite_comparison(price,v.opposite_operator(chart.last_pivot(v.continue_trend).price,self.continuation)):
                    # Rule 10.(g)/10.(i)
                    warning = Warning(chart.last_trend(),chart.last_pivot(v.continue_trend),'continuation')
                v.signal(self.date,chart.last_pivot(v.continue_trend).price,v.memo,v.rule)
            elif (chart.last_pivot(chart.last_trend()) is not None and 
                chart.last_pivot(v.opposing_trend) is not None and 
                v.opposite_comparison(chart.last_pivot(v.opposing_trend).price,chart.last_pivot(chart.last_trend()).price) and
                v.comparison_eq(price,v.opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation))):
                # Rule 5.(a)/5.(b)
                trend = v.continue_trend
                v.signal(self.date,v.opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation),v.memo_continue,v.rule_continue)
            else:
                # Rule 6.(a)/6.(c)
                trend = chart.last_trend()
        else:
            price = opposite_level
            adjusted_price = adjusted_opposite_level
            if (chart.active_warning() is not None and 
                chart.active_warning().trend == v.continue_trend and 
                v.opposite_comparison_eq(price,v.operator(chart.last_pivot(v.continue_trend).price,self.continuation))):
                    # Rule 10.(e)/10.(f)
                    chart.cancel_warning()
                    v.opposite_signal(self.date,v.operator(chart.last_pivot(v.continue_trend).price,self.continuation),v.memo_warning,v.rule_warning)
            if chart.last_pivot(v.reversal_trend) is not None and v.opposite_comparison_eq(price,chart.last_pivot(v.reversal_trend).price):
                trend = v.reversal_trend
                if v.comparison(opposite_level,v.operator(chart.last_pivot(v.reversal_trend).price,self.continuation)):
                    # Rule 10.(e)/10.(f)
                    warning = Warning(v.reversal_trend,chart.last_pivot(v.reversal_trend),'continuation')
                # Rule 6.(b)/6.(d)
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),v.rule_followthrough,chart.last_adjusted_price())
            elif v.opposite_comparison(price,v.operator(chart.last_price(),self.reversal)):
                if chart.last_pivot(v.opposing_trend) is not None and v.comparison(price,chart.last_pivot(v.opposing_trend).price):
                    # Rule 6.(g)/6.(h)
                    trend = v.secondary_trend
                    chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),v.rule_pivot_secondary,chart.last_adjusted_price())
                else:
                    trend = v.opposing_trend
                    chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),v.rule_pivot,chart.last_adjusted_price())
        return price, adjusted_price, trend, warning

    def _secondary_trend(self,chart):
        adjusted_price, price, trend = (None, None, None)
        v = DatapointVariables()
        v.trend(chart.last_trend(),chart)
        if chart.last_trend() == SECONDARY_RALLY:
            level = self.high
            adjusted_level = self.adjusted_high
            opposite_level = self.low
            adjusted_opposite_level = self.adjusted_low
        else: # SECONDARY_REACTION
            level = self.low
            adjusted_level = self.adjusted_low
            opposite_level = self.high
            adjusted_opposite_level = self.adjusted_high
        if v.comparison(level,chart.last_price()):
            price = level
            adjusted_price = adjusted_level
            if chart.last_pivot(v.continue_trend) is not None and v.comparison(price,chart.last_pivot(v.continue_trend).price):
                # Rule 6.(b)/6.(d)
                trend = v.continue_trend
                v.signal(self.date,chart.last_pivot(v.continue_trend).price,v.memo,v.rule)
            elif v.comparison(price,chart.last_pivot(v.confirmation_trend).price):
                # Rule 6.(g)/6.(h)
                trend = v.confirmation_trend
            else:
                # Rule 6.(g)/6.(h)
                trend = chart.last_trend()
        elif v.opposite_comparison_eq(opposite_level,chart.last_price()):
            price = opposite_level
            adjusted_price = adjusted_opposite_level
            if chart.last_pivot(v.reversal_trend) is not None and v.opposite_comparison(price,chart.last_pivot(v.reversal_trend).price):
                # Rule 6.(b)/6.(d)
                trend = v.reversal_trend
                v.opposite_signal(self.date,chart.last_pivot(v.reversal_trend).price,v.memo_reversal,v.rule_reversal)
                chart.add_pivot(chart.last_date(),chart.last_price(),v.confirmation_trend,v.rule_pivot,chart.last_adjusted_price())
            elif chart.last_pivot(v.countertrend) is not None and v.opposite_comparison_eq(price,chart.last_pivot(v.countertrend).price):
                trend = v.countertrend
                chart.add_pivot(chart.last_date(),chart.last_price(),v.confirmation_trend,v.rule_pivot,chart.last_adjusted_price())
        return price, adjusted_price, trend, None

    def _added_signals(self,chart,previous_entry):
        previous_trend = previous_entry.trend
        last_entry = chart.last_entry()
        v = DatapointVariables()
        for i in range(2):
            if i == 0: 
                v.pivot(previous_trend,chart,'trend')
                warning = previous_entry.pivot_warning
                warning_set = last_entry.set_pivot_warning
            else:
                v.pivot(previous_trend,chart,'countertrend')
                warning = previous_entry.counterpivot_warning
                warning_set = last_entry.set_counterpivot_warning
            pivots = self._evaluate_pivots(v.comparison,v.trend_pivots,v.natural_pivots)
            for pivot in pivots:
                if v.comparison(last_entry.price,previous_entry.price):
                    # Movement in same direction as previous trend
                    if warning is not None:
                        # Pivot warning in effect for previous trend
                        if warning.trend == previous_trend and warning.pivot is pivot:
                            # Pivot warning was for this pivot
                            if (warning.subtype == 'short distance' and 
                                v.comparison_eq(last_entry.price,v.opposite_operator(pivot.price,self.short_distance)) and 
                                v.opposite_comparison(last_entry.price,pivot.price)):
                                # "Short distance" warning still in effect
                                warning_set(last_entry.trend,pivot,warning.subtype)
                                break
                            elif v.opposite_comparison(last_entry.price,v.operator(pivot.price,self.continuation)):
                                # "Continuation" warning now/still in effect
                                warning_set(last_entry.trend,pivot,'continuation')
                                break
                            else:
                                # Pivot breakout; warning cancelled
                                v.signal(self.date,v.operator(pivot.price,self.continuation),v.breakout_memo,v.breakout_rule)
                                continue
                    if v.comparison(pivot.price,last_entry.price):
                        # Pivot price beyond last price
                        if (v.comparison_eq(last_entry.price,v.opposite_operator(pivot.price,self.short_distance)) and 
                            v.opposite_comparison(last_entry.price,pivot.price)):
                            # Last price within "short distance", triggering pivot warning
                            warning_set(last_entry.trend,pivot,'short_distance')
                            break
                    else:
                        # Pivot price within last price
                        if v.opposite_comparison(last_entry.price,v.operator(pivot.price,self.continuation)):
                            # Last price within "continuation", triggering pivot warning
                            warning_set(last_entry.trend,pivot,'continuation')
                            break
                        elif v.comparison(pivot.price,previous_entry.price):
                            # Pivot breakout
                            v.signal(self.date,v.operator(pivot.price,self.continuation),v.breakout_memo,v.breakout_rule)
                else:
                    # Movement in direction contrary to previous trend
                    if warning is not None:
                        # Pivot warning in effect for previous trend
                        if warning.trend == previous_trend and warning.pivot is pivot:
                            # Pivot warning was for this pivot
                            if v.opposite_comparison(last_entry.price,v.opposite_operator(pivot.price,self.continuation)):
                                # Reversal
                                if warning.subtype == 'short distance':
                                    memo = v.reversal_short_distance_memo
                                    rule = v.reversal_short_distance_rule
                                else:
                                    memo = v.reversal_continuation_memo
                                    rule = v.reversal_continuation_rule
                                v.opposite_signal(self.date,v.opposite_operator(pivot.price,self.continuation),memo,rule)
                                continue
                            elif (warning.subtype == 'short distance' and
                                v.comparison_eq(last_entry.price,v.opposite_operator(pivot.price,self.short_distance)) and 
                                v.opposite_comparison(last_entry.price,pivot.price)):
                                # Short distance warning still in effect
                                warning_set(last_entry.trend,pivot,warning.subtype)
                                break
                            else:
                                # Continuation warning
                                warning_set(last_entry.trend,pivot,'continuation')
                                break

    def _evaluate_pivots(self,comparison,trend_object=None,natural_object=None):
        pivots = []
        return_pivots = []
        if trend_object is not None:
            trend_pivots = trend_object(all=True)
            if trend_pivots is not None:
                pivots = pivots + trend_pivots[1:]
        if natural_object is not None:
            natural_pivots = natural_object(all=True)
            if natural_pivots is not None:
                pivots = pivots + natural_pivots[1:]
        if pivots and len(pivots) > 1:
            pivots.sort(key=lambda x: x.date, reverse=True)
            for pivot in pivots:
                if dt.strptime(pivot.date, "%Y-%m-%d") < self.oldest_pivot:
                    # Pivot out of date range
                    break
                if return_pivots:
                    length = len(return_pivots)
                    excluded = False
                    for i in range(0, length):
                        diff = 0
                        if self.pivot_price_logic == PIVOT_PRICE_ADJUSTED:
                            diff = abs(pivot.adjusted_price - return_pivots[i].adjusted_price)
                        else: # PIVOT_PRICE_ORIGINAL
                            diff = abs(pivot.price - return_pivots[i].price)
                        if diff <= self.continuation:
                            if self.pivot_logic == PIVOT_LOGIC_OUTER:
                                if self.pivot_price_logic == PIVOT_PRICE_ADJUSTED:
                                    if comparison(pivot.adjusted_price, return_pivots[i].adjusted_price):
                                        excluded = True
                                        return_pivots.pop(i)
                                        return_pivots.append(pivot)
                                        break
                                    else:
                                        excluded = True
                                        break
                                else: # PIVOT_PRICE_ORIGINAL
                                    if comparison(pivot.price, return_pivots[i].price):
                                        excluded = True
                                        return_pivots.pop(i)
                                        return_pivots.append(pivot)
                                        break
                                    else:
                                        excluded = True
                                        break
                            else: # PIVOT_LOGIC_RECENT:
                                excluded = True
                                break
                        else: # price of pivot outside continuation range
                            continue
                    if not excluded:
                        return_pivots.append(pivot)
                else:
                    return_pivots.append(pivot)
        return return_pivots

    def _nearest_extended_pivots(self,chart,price):
        nearest_pivot = {}
        nearest_pivot['upward'] = {}
        nearest_pivot['downward'] = {}
        for pivot_type in ['upward','downward']:
            if pivot_type == 'upward':
                type_pivots = self._evaluate_pivots(self._gt,chart.last_upward_pivot,chart.last_rally_pivot)
            else:
                type_pivots = self._evaluate_pivots(self._lt,chart.last_downward_pivot,chart.last_reaction_pivot)
            if type_pivots is not None:
                type_pivots.sort(key=lambda x: x.price)
                for pivot in type_pivots:
                    if pivot.price < price: 
                        if pivot.trend in nearest_pivot['downward']:
                            if pivot.price > nearest_pivot['downward'][pivot.trend].price:
                                nearest_pivot['downward'][pivot.trend] = pivot
                        else:
                            nearest_pivot['downward'][pivot.trend] = pivot
                    elif pivot.price > price: 
                        if pivot.trend in nearest_pivot['upward']:
                            if pivot.price < nearest_pivot['upward'][pivot.trend].price:
                                nearest_pivot['upward'][pivot.trend] = pivot
                        else:
                            nearest_pivot['upward'][pivot.trend] = pivot
        return nearest_pivot

    def _gt(self,val1,val2):
        return (val1 > val2)

    def _lt(self,val1,val2):
        return (val1 < val2)

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
        latest = kwargs.get('latest',False)
        thresholds = kwargs.get('thresholds',THRESHOLDS)

        # Create storage
        self.chart = Chart() 
        self.chart.add_meta('Thresholds',thresholds)

        # Get symbol/price data
        daily_price_series = self.price_object.daily(self.symbol,regen=self.regen)
        if daily_price_series is None:
            raise Exception('Daily price series for ' + self.symbol + ' not located for date range.')

        # Add realtime data point if requested
        latest_added = False
        if latest is True:
            latest_quote = self.price_object.latest(self.symbol)
            latest_date = dt.strptime(latest_quote['date'], "%Y-%m-%d")

        # Evaluate
        datapoint = None
        for date, price in daily_price_series.items():
            if latest is True:
                if latest_date == dt.strptime(date, "%Y-%m-%d"):
                    datapoint = Datapoint(date,latest_quote,thresholds)
                    latest_added = True
                else:
                    datapoint = Datapoint(date,price,thresholds)
            else:
                datapoint = Datapoint(date,price,thresholds)
            if self.chart.empty():
                # Starting price (use closing price, but only to INITIATE records)
                self.chart.add_date(date,datapoint.close,datapoint.adjusted_close)
            elif self.chart.last_trend() is None:
                # Starting trend
                last_entry = self.chart.last_entry()
                if datapoint.close > last_entry.price:
                    self.chart.add_date(date,datapoint.high,datapoint.adjusted_high,UPWARD_TREND)
                    self.chart.add_pivot(date,datapoint.low,DOWNWARD_TREND,'11b',datapoint.adjusted_low)
                elif datapoint.close < last_entry.price:
                    self.chart.add_date(date,datapoint.low,datapoint.adjusted_low,DOWNWARD_TREND)
                    self.chart.add_pivot(date,datapoint.high,UPWARD_TREND,'11c',datapoint.adjusted_high)
            else:
                datapoint.chart(self.chart)
        if latest is True and latest_added is False:
            datapoint = Datapoint(latest_quote['date'],latest_quote,thresholds)
            datapoint.chart(self.chart)
        if datapoint is not None:
            datapoint.watch(self.chart)
        return self.chart
