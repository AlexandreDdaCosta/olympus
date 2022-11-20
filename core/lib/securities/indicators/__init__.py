import json, re, types

from datetime import datetime as dt
from decimal import Decimal

from olympus import Return, Series

DEFAULT_ATR_PERIODS = 20
MINIMUM_ATR_PERIODS = 8
MAXIMUM_ATR_PERIODS = 50

DEFAULT_MOVING_AVERAGE_TYPE = 'Simple'
DEFAULT_MOVING_AVERAGE_PERIODS = 50
MINIMUM_MOVING_AVERAGE_PERIODS = 8
MAXIMUM_MOVING_AVERAGE_PERIODS = 200
VALID_MOVING_AVERAGE_TYPES = ['Exponential', 'Hull', 'Simple']

PRICE_ROUNDER = 6

class AverageTrueRange(Series):
    # Calculates periodic true range and average true range for a price series

    def __init__(self,price_series,**kwargs):
        super(AverageTrueRange,self).__init__()
        periods = int(kwargs.pop('periods', DEFAULT_ATR_PERIODS))
        if periods < MINIMUM_ATR_PERIODS or periods > MAXIMUM_ATR_PERIODS:
            raise Exception('Parameter for "periods" (%s) is not within the available range: %s to %s' % (periods,MINIMUM_ATR_PERIODS,MAXIMUM_ATR_PERIODS))
        price_series.sort()
        quote = price_series.next(reset=True)
        atr_sum = Decimal('0.0')
        atr_sum_adjusted = Decimal('0.0')
        period = 1
        previous_quote = None
        last_atr = None
        last_atr_adjusted = None
        while quote is not None:
            atr_entry = types.SimpleNamespace()
            atr_entry.date = quote.date
            atr_entry.true_range = self._round(self._true_range(quote,previous_quote))
            atr_entry.true_range_adjusted = self._round(self._true_range(quote,previous_quote,True))
            if period <= periods:
                atr_sum = atr_sum + Decimal(str(atr_entry.true_range))
                atr_entry.atr = self._round(atr_sum / period)
                atr_sum_adjusted = atr_sum_adjusted + Decimal(str(atr_entry.true_range_adjusted))
                atr_entry.atr_adjusted = self._round(atr_sum_adjusted / period)
                if period == periods:
                    last_atr = Decimal(atr_entry.atr)
                    last_atr_adjusted = Decimal(atr_entry.atr_adjusted)
                period = period + 1
            else:
                last_atr = ((last_atr * (periods - 1)) + Decimal(atr_entry.true_range)) / periods 
                last_atr_adjusted = ((last_atr_adjusted * (periods - 1)) + Decimal(atr_entry.true_range_adjusted)) / periods
                atr_entry.atr = self._round(last_atr)
                atr_entry.atr_adjusted = self._round(last_atr_adjusted)
            self.add(atr_entry)
            previous_quote = quote
            quote = price_series.next()

    def _round(self,value):
        return round(float(value), PRICE_ROUNDER)

    def _true_range(self,quote,previous_quote=None,adjusted=False):
        if adjusted is False:
            if previous_quote is not None:
                return max( Decimal(str(quote.high)) - Decimal(str(quote.low)), abs(Decimal(str(quote.low)) - Decimal(str(previous_quote.close))), abs(Decimal(str(quote.high)) - Decimal(str(previous_quote.close))))
            else:
                return Decimal(str(quote.high)) - Decimal(str(quote.low))
        else:
            if previous_quote is not None:
                if quote.adjusted_high is None:
                    if previous_quote.adjusted_high is None:
                        return max( Decimal(str(quote.high)) - Decimal(str(quote.low)), abs(Decimal(str(quote.low)) - Decimal(str(previous_quote.close))), abs(Decimal(str(quote.high)) - Decimal(str(previous_quote.close))))
                    else:
                        return max( Decimal(str(quote.high)) - Decimal(str(quote.low)), abs(Decimal(str(quote.low)) - Decimal(str(previous_quote.adjusted_close))), abs(Decimal(str(quote.high)) - Decimal(str(previous_quote.adjusted_close))))
                else:
                    if previous_quote.adjusted_high is None:
                        raise Exception('Quotes with adjusted values should not have earlier quotes with unadjusted values.')
                    else:
                        return max( Decimal(str(quote.adjusted_high)) - Decimal(str(quote.adjusted_low)), abs(Decimal(str(quote.adjusted_low)) - Decimal(str(previous_quote.adjusted_close))), abs(Decimal(str(quote.adjusted_high)) - Decimal(str(previous_quote.adjusted_close))))
            else:
                if quote.adjusted_high is None:
                    return Decimal(str(quote.high)) - Decimal(str(quote.low))
                else:
                    return Decimal(str(quote.adjusted_high)) - Decimal(str(quote.adjusted_low))

class MovingAverage(Series):
    # Calculates various periodic moving average types for a price series

    def __init__(self,price_series,**kwargs):
        super(MovingAverage,self).__init__()
        periods = int(kwargs.pop('periods', DEFAULT_MOVING_AVERAGE_PERIODS))
        average_type = kwargs.pop('average_type', DEFAULT_MOVING_AVERAGE_TYPE)
        if periods < MINIMUM_MOVING_AVERAGE_PERIODS or periods > MAXIMUM_MOVING_AVERAGE_PERIODS:
            raise Exception('Parameter for "periods" (%s) is not within the available range: %s to %s' % (periods,MINIMUM_MOVING_AVERAGE_PERIODS,MAXIMUM_MOVING_AVERAGE_PERIODS))
        if average_type not in VALID_MOVING_AVERAGE_TYPES:
            raise Exception('Parameter for "average_type" (%s) is invalid; choose from the following: %s' % (average_type,', '.join(VALID_MOVING_AVERAGE_TYPES)) )
        price_series.sort()
        try:
            func = getattr(self,'_'+average_type.lower())
        except AttributeError:
            raise Exception('Function for average "%s" not found.' % (average_type) )
        else:
            func(price_series,periods)

    def _exponential(self,price_series,periods):
        quote = price_series.next(reset=True)
        while quote is not None:
            quote = price_series.next()

    def _hull(self,price_series,periods):
        quote = price_series.next(reset=True)
        while quote is not None:
            quote = price_series.next()

    def _simple(self,price_series,periods):
        quote = price_series.next(reset=True)
        period = 1
        quotes = []
        quotes_adjusted = []
        while quote is not None:
            if period <= periods:
                period = period + 1
            else:
                quotes.pop()
            quotes.append(quote.close)
            if quote.adjusted_close is not None:
                quotes_adjusted.append(quote.adjusted_close)
            else:
                quotes_adjusted.append(quote.close)
            ma_entry = types.SimpleNamespace()
            ma_entry.date = quote.date
            ma_entry.moving_average = sum(quotes) / len(quotes)
            ma_entry.moving_average_adjusted = sum(quotes_adjusted) / len(quotes_adjusted)
            self.add(ma_entry)
            quote = price_series.next()

class RiskRange():

# Calculates tradeable risk ranges for securities based on price, volume, and historic volatility

    pass
