import json

from datetime import datetime as dt
from operator import itemgetter

import olympus.equities_us.data.price as price
import olympus.equities_us.data.symbols as symbols

from larry import *

class Alert(object):

    def __init__(self,price,subtype,rule):
        self.price = price
        self.subtype = subtype
        self.rule = rule

    def __repr__(self):
        return "Alert(price=%.2f,type=%r,rule=%r)" % (self.price,self.subtype,self.rule)

class Date(object):

    def __init__(self,date,price,adjusted_price,trend,warning=None):
        self.date = date
        self.price = price
        self.adjusted_price = adjusted_price
        self.trend = trend
        self.warning = warning

    def __repr__(self):
        if self.warning is not None:
            return "Date(date=%r,price=%.2f,adjusted_price=%.2f,trend=%r,warning=%r)" % (self.date,self.price,self.adjusted_price,self.trend,self.warning)
        return "Date(date=%r,price=%.2f,adjusted_price=%.2f,trend=%r)" % (self.date,self.price,self.adjusted_price,self.trend)

    def reset_warning(self):
        self.warning = None

class Pivot(object):

    def __init__(self,date,price,subtype,rule,adjusted_price):
        self.date = date
        self.price = price
        self.subtype = subtype
        self.rule = rule
        self.adjusted_price = adjusted_price

    def __repr__(self):
        return "Pivot(date=%r,price=%.2f,type=%r,rule=%r,adjusted_price=%.2f)" % (self.date,self.price,self.subtype,self.rule,self.adjusted_price)

class Signal(object):

    def __init__(self,date,price,subtype,memo,rule):
        self.date = date
        self.price = price
        self.subtype = subtype
        self.memo = memo
        self.rule = rule

    def __repr__(self):
        return "Signal(date=%r,price=%.2f,type=%r,memo=%r,rule=%r)" % (self.date,self.price,self.subtype,self.memo,self.rule)

class Chart(object):

    def __init__(self,**kwargs):
        self.meta = { 'Date': dt.now().strftime('%Y-%m-%d %H:%M:%S.%f') }
        self.alerts = { BUY: [], SELL: [] }
        self.dates = []
        self.pivots = { UPWARD_TREND: [], DOWNWARD_TREND: [], NATURAL_RALLY: [], NATURAL_REACTION: [] }
        self.signals = { BUY: [], SELL: [] }
    
    def active_warning(self):
        entry = self.last_entry()
        if entry is not None and entry.warning is not None:
            return entry.warning
        return None
    
    def add_alert(self,price,subtype,rule):
        alert = Alert(price,subtype,rule)
        self.alerts[subtype].append(alert)
    
    def add_date(self,date,price,adjusted_price,trend=None,warning=None):
        date = Date(date,price,adjusted_price,trend,warning)
        self.dates.append(date)
    
    def add_meta(self,key,data):
        self.meta[key] = data
    
    def add_pivot(self,date,price,subtype,rule,adjusted_price):
        pivot = Pivot(date,price,subtype,rule,adjusted_price)
        self.pivots[subtype].append(pivot)
    
    def buy_alerts(self):
        if self.alerts[BUY]:
            return self.alerts[BUY]
        return None

    def buy_signal(self,date,price,memo,rule=None):
        return self._add_signal(date,price,BUY,memo,rule)

    def cancel_warning(self):
        if self.dates:
            self.dates[-1].reset_warning()
    
    def empty(self):
        if self.dates:
            return False
        return True

    def has_pivot(self,subtype):
        if self.pivots[subtype]:
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

    def last_pivot(self,subtype):
        if self.pivots[subtype]:
            return self.pivots[subtype][-1]
        return None

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

    def sell_alerts(self):
        if self.alerts[SELL]:
            return self.alerts[SELL]
        return None

    def sell_signal(self,date,price,memo,rule=None):
        return self._add_signal(date,price,SELL,memo,rule)

    def _add_signal(self,date,price,subtype,memo,rule):
        signal = Signal(date,price,subtype,memo,rule)
        self.signals[subtype].append(signal)
    
    def _last_pivot(self,subtype,quantity,**kwargs):
        all = kwargs.get('all',False)
        if self.pivots[subtype]:
            if all is True:
                return self.pivots[subtype]
            else:
                return self.pivots[subtype][-quantity:]
        return None
    
    def _last_signal(self,subtype,quantity,**kwargs):
        all = kwargs.get('all',False)
        if self.signals[subtype]:
            if all is True:
                return self.signals[subtype]
            else:
                return self.signals[subtype][-quantity:]
        return None

class Datapoint(object):
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition
    # 
    # Numbered rules:
    # 
    # 1-10: See Chapter 10, "Explanatory Rules", pp. 91-101
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

    def __init__(self,date,datapoint,thresholds,**kwargs):
        self.date = date
        print(datapoint)
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

    def alerts(self,chart):
        #ALEX
        return None

    def chart(self,chart,**kwargs):
        # Three major categories of price trend, each with two trends of similar logic but with logical comparisons reversed
        if chart.last_trend() == UPWARD_TREND or chart.last_trend() == DOWNWARD_TREND:
            trend = self._trend
        elif chart.last_trend() == NATURAL_RALLY or chart.last_trend() == NATURAL_REACTION:
            trend = self._countertrend
        elif chart.last_trend() == SECONDARY_RALLY or chart.last_trend() == SECONDARY_REACTION:
            trend = self._secondary_trend
        price, adjusted_price, trend, warning = trend(chart)
        if trend is not None:
            chart.add_date(self.date,price,adjusted_price,trend,warning)
        self._added_signals(self.date,chart)

    def _added_signals(self,date,chart):
        #ALEX
        return None

    def _trend(self,chart):
        adjusted_price, price, trend, warning = (None, None, None, None)
        # Defaults are for trend continuation, "opposite" for opposing trend or action
        if chart.last_trend() == UPWARD_TREND:
            comparison = self._gt
            opposite_comparison = self._lt
            level = self.high
            adjusted_level = self.adjusted_high
            opposite_level = self.low
            adjusted_opposite_level = self.adjusted_low
            memo = 'Reaction to Upward'
            operator = self._add
            opposite_operator = self._subtract
            rule = '10a'
            opposite_rule = '10b'
            signal = chart.buy_signal
            opposite_signal = chart.sell_signal
            countertrend = DOWNWARD_TREND
            countertrend_memo = 'Upward to Downward'
            countertrend_rule = '12a'
            natural_countertrend = NATURAL_REACTION
            natural_countertrend_rule = '6a'
            reversal_comparison = self._lteq
        else: # DOWNWARD_TREND
            comparison = self._lt
            opposite_comparison = self._gt
            level = self.low
            adjusted_level = self.adjusted_low
            opposite_level = self.high
            adjusted_opposite_level = self.adjusted_high
            memo = 'Rally to Downward'
            operator = self._subtract
            opposite_operator = self._add
            rule = '10c'
            opposite_rule = '10d'
            signal = chart.sell_signal
            opposite_signal = chart.buy_signal
            countertrend = UPWARD_TREND
            countertrend_memo = 'Downward to Upward'
            countertrend_rule = '12b'
            natural_countertrend = NATURAL_RALLY
            natural_countertrend_rule = '6c'
            reversal_comparison = self._gteq
        opposite_memo = memo + ' Failure'
        if comparison(level,chart.last_price()):
            # Rule 1/2
            price = level
            adjusted_price = adjusted_level
            trend = chart.last_trend()
            if chart.active_warning() is not None and chart.active_warning() == chart.last_trend():
                # Rule 10.(a)/10.(c)
                if opposite_comparison(price,operator(chart.last_pivot(chart.last_trend()).price,self.continuation)):
                    warning = chart.last_trend()
                else:
                    signal(self.date,operator(chart.last_pivot(chart.last_trend()).price,self.continuation),memo,rule)
        else:
            price = opposite_level
            adjusted_price = adjusted_opposite_level
            if (chart.active_warning() is not None and 
                chart.active_warning() == chart.last_trend() and 
                opposite_comparison(price,opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation))):
                # Rule 10.(b)/10.(d)
                chart.cancel_warning()
                opposite_signal(self.date,opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation),opposite_memo,opposite_rule)
            if chart.last_pivot(countertrend) is not None and opposite_comparison(price,chart.last_pivot(countertrend).price):
                # Rule 12.(a)/12.(b)
                trend = countertrend
                opposite_signal(self.date,chart.last_pivot(countertrend).price,countertrend_memo,countertrend_rule)
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),countertrend_rule,chart.last_adjusted_price())
            elif reversal_comparison(price,opposite_operator(chart.last_price(),self.reversal)):
                # Rule 6.(a)/6.(c)
                trend = natural_countertrend
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),natural_countertrend_rule,chart.last_adjusted_price())
        return price, adjusted_price, trend, warning

    def _countertrend(self,chart):
        adjusted_price, price, trend, warning = (None, None, None, None)
        if chart.last_trend() == NATURAL_RALLY:
            comparison = self._gt
            opposite_comparison = self._lt
            comparison_eq = self._gteq
            opposite_comparison_eq = self._lteq
            level = self.high
            adjusted_level = self.adjusted_high
            opposite_level = self.low
            adjusted_opposite_level = self.adjusted_low
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
            rule_pivot = '4d'
            rule_pivot_secondary = '13b'
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
            adjusted_level = self.adjusted_low
            opposite_level = self.high
            adjusted_opposite_level = self.adjusted_high
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
            rule_pivot = '4b'
            rule_pivot_secondary = '13a'
            continue_trend = DOWNWARD_TREND
            reversal_trend = UPWARD_TREND
            opposing_trend = NATURAL_RALLY
            secondary_trend = SECONDARY_RALLY
        if comparison(level,chart.last_price()):
            price = level
            adjusted_price = adjusted_level
            if (chart.last_pivot(continue_trend) is not None and 
                comparison_eq(price,operator(chart.last_pivot(continue_trend).price,self.short_distance)) and 
                opposite_comparison(price,chart.last_pivot(continue_trend).price)):
                # Rule 10.(e)/10.(f)
                warning = continue_trend
            if chart.last_pivot(continue_trend) is not None and comparison_eq(price,chart.last_pivot(continue_trend).price):
                # Rule 6.(e)/6.(f)
                trend = continue_trend
                signal(self.date,chart.last_pivot(continue_trend).price,memo,rule)
            elif (chart.last_pivot(chart.last_trend()) is not None and 
                chart.last_pivot(opposing_trend) is not None and 
                opposite_comparison(chart.last_pivot(opposing_trend).price,chart.last_pivot(chart.last_trend()).price) and
                comparison_eq(price,opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation))):
                # Rule 5.(a)/5.(b)
                trend = continue_trend
                signal(self.date,opposite_operator(chart.last_pivot(chart.last_trend()).price,self.continuation),memo_continue,rule_continue)
            else:
                # Rule 6.(a)/6.(c)
                trend = chart.last_trend()
        else:
            price = opposite_level
            adjusted_price = adjusted_opposite_level
            if (chart.active_warning() is not None and 
                chart.active_warning() == continue_trend and 
                opposite_comparison_eq(price,operator(chart.last_pivot(continue_trend).price,self.continuation))):
                    # Rule 10.(e)/10.(f)
                    chart.cancel_warning()
                    opposite_signal(self.date,operator(chart.last_pivot(continue_trend).price,self.continuation),memo_warning,rule_warning)
            if chart.last_pivot(reversal_trend) is not None and opposite_comparison_eq(price,chart.last_pivot(reversal_trend).price):
                trend = reversal_trend
                if comparison(opposite_level,operator(chart.last_pivot(reversal_trend).price,self.continuation)):
                    # Rule 10.(e)/10.(f)
                    warning = reversal_trend
                # Rule 6.(b)/6.(d)
                chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),rule_followthrough,chart.last_adjusted_price())
            elif opposite_comparison(price,operator(chart.last_price(),self.reversal)):
                if chart.last_pivot(opposing_trend) is not None and comparison(price,chart.last_pivot(opposing_trend).price):
                    # Rule 6.(g)/6.(h)
                    trend = secondary_trend
                    chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),rule_pivot_secondary,chart.last_adjusted_price())
                else:
                    trend = opposing_trend
                    chart.add_pivot(chart.last_date(),chart.last_price(),chart.last_trend(),rule_pivot,chart.last_adjusted_price())
        return price, adjusted_price, trend, warning

    def _secondary_trend(self,chart):
        adjusted_price, price, trend = (None, None, None)
        if chart.last_trend() == SECONDARY_RALLY:
            comparison = self._gt
            opposite_comparison = self._lt
            opposite_comparison_eq = self._lteq
            level = self.high
            adjusted_level = self.adjusted_high
            opposite_level = self.low
            adjusted_opposite_level = self.adjusted_low
            signal = chart.buy_signal
            opposite_signal = chart.sell_signal
            memo = 'Secondary Rally to Upward'
            rule = '6d'
            memo_reversal = 'Secondary Rally to Downward'
            rule_reversal = '6h'
            rule_pivot = '13d'
            continue_trend = UPWARD_TREND
            reversal_trend = DOWNWARD_TREND
            confirmation_trend = NATURAL_RALLY
            countertrend = NATURAL_REACTION
        else: # SECONDARY_REACTION
            comparison = self._lt
            opposite_comparison = self._gt
            opposite_comparison_eq = self._gteq
            level = self.low
            adjusted_level = self.adjusted_low
            opposite_level = self.high
            adjusted_opposite_level = self.adjusted_high
            signal = chart.sell_signal
            opposite_signal = chart.buy_signal
            memo = 'Secondary Reaction to Downward'
            rule = '6b'
            memo_reversal = 'Secondary Reaction to Upward'
            rule_reversal = '6g'
            rule_pivot = '13c'
            continue_trend = DOWNWARD_TREND
            reversal_trend = UPWARD_TREND
            confirmation_trend = NATURAL_REACTION
            countertrend = NATURAL_RALLY
        if comparison(level,chart.last_price()):
            price = level
            adjusted_price = adjusted_level
            if chart.last_pivot(continue_trend) is not None and comparison(price,chart.last_pivot(continue_trend).price):
                # Rule 6.(b)/6.(d)
                trend = continue_trend
                signal(self.date,chart.last_pivot(continue_trend).price,memo,rule)
            elif comparison(price,chart.last_pivot(confirmation_trend).price):
                # Rule 6.(g)/6.(h)
                trend = confirmation_trend
            else:
                # Rule 6.(g)/6.(h)
                trend = chart.last_trend()
        elif opposite_comparison_eq(opposite_level,chart.last_price()):
            price = opposite_level
            adjusted_price = adjusted_opposite_level
            if chart.last_pivot(reversal_trend) is not None and opposite_comparison(price,chart.last_pivot(reversal_trend).price):
                # Rule 6.(b)/6.(d)
                trend = reversal_trend
                opposite_signal(self.date,chart.last_pivot(reversal_trend).price,memo_reversal,rule_reversal)
                chart.add_pivot(chart.last_date(),chart.last_price(),confirmation_trend,rule_pivot,chart.last_adjusted_price())
            elif chart.last_pivot(countertrend) is not None and opposite_comparison_eq(price,chart.last_pivot(countertrend).price):
                trend = countertrend
                chart.add_pivot(chart.last_date(),chart.last_price(),confirmation_trend,rule_pivot,chart.last_adjusted_price())
        return price, adjusted_price, trend, None

    def _add(self,val1,val2):
        return (val1 + val2)

    def _subtract(self,val1,val2):
        return (val1 - val2)

    def _gt(self,val1,val2):
        return (val1 > val2)

    def _gteq(self,val1,val2):
        return (val1 >= val2)

    def _lt(self,val1,val2):
        return (val1 < val2)

    def _lteq(self,val1,val2):
        return (val1 <= val2)

class Calculate(object):
    # Generate summary associated with the Livermore Market Key.
    # For an example of the original Livermore paper charts, see 
    # Jesse L. Livermore, "How to Trade in Stocks", First Edition, pp. 102-133

    def __init__(self,symbol=SYMBOL,user=USER,**kwargs):
        self.user = user
        self.regen = kwargs.get('regen',False)
        self.regen = True
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
            datapoint.alerts(self.chart)
        return self.chart

