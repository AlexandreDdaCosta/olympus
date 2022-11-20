import json, re, types

from datetime import datetime as dt
from decimal import Decimal

from olympus import Return, Series

DEFAULT_ATR_PERIODS = 20
MINIMUM_ATR_PERIODS = 8
MAXIMUM_ATR_PERIODS = 50

DEFAULT_MOVING_AVERAGE_TYPE = 'Simple'
DEFAULT_MOVING_AVERAGE_LENGTH = 50
VALID_MOVING_AVERAGE_TYPES = ['Exponential', 'Hull', 'Simple']

class AverageTrueRange(Series):

    def __init__(self,price_series,**kwargs):
        super(AverageTrueRange,self).__init__()
        periods = kwargs.pop('periods', DEFAULT_ATR_PERIODS)
        if periods < MINIMUM_ATR_PERIODS or periods > MAXIMUM_ATR_PERIODS:
            raise Exception('Parameter for "periods" (' + periods + ') is not within the available range: ' + str(MINIMUM_ATR_PERIODS) + ' to ' + str(MAXIMUM_ATR_PERIODS))
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
            atr_entry.true_range = self._true_range(quote,previous_quote)
            atr_entry.true_range_adjusted = self._true_range(quote,previous_quote,True)
            if period <= periods:
                atr_sum = atr_sum + Decimal(str(atr_entry.true_range))
                atr_entry.atr = round(float(atr_sum / period), 2)
                atr_sum_adjusted = atr_sum_adjusted + Decimal(str(atr_entry.true_range_adjusted))
                atr_entry.atr_adjusted = round(float(atr_sum_adjusted / period), 2)
                if period == periods:
                    last_atr = Decimal(atr_entry.atr)
                    last_atr_adjusted = Decimal(atr_entry.atr_adjusted)
                period = period + 1
            else:
                last_atr = ((last_atr * (periods - 1)) + Decimal(atr_entry.true_range)) / periods 
                last_atr_adjusted = ((last_atr_adjusted * (periods - 1)) + Decimal(atr_entry.true_range_adjusted)) / periods
                atr_entry.atr = round(float(last_atr), 2)
                atr_entry.atr_adjusted = round(float(last_atr_adjusted), 2)
            self.add(atr_entry)
            print(atr_entry)
            previous_quote = quote
            quote = price_series.next()

    def _true_range(self,quote,previous_quote=None,adjusted=False):
        if adjusted is False:
            if previous_quote is not None:
                return max( float(Decimal(str(quote.high)) - Decimal(str(quote.low))), abs(float(Decimal(str(quote.low)) - Decimal(str(previous_quote.close)))), abs(float(Decimal(str(quote.high)) - Decimal(str(previous_quote.close)))))
            else:
                return float(Decimal(str(quote.high)) - Decimal(str(quote.low)))
        else:
            if previous_quote is not None:
                if quote.adjusted_high is None:
                    if previous_quote.adjusted_high is None:
                        return max( float(Decimal(str(quote.high)) - Decimal(str(quote.low))), abs(float(Decimal(str(quote.low)) - Decimal(str(previous_quote.close)))), abs(float(Decimal(str(quote.high)) - Decimal(str(previous_quote.close)))))
                    else:
                        return max( float(Decimal(str(quote.high)) - Decimal(str(quote.low))), abs(float(Decimal(str(quote.low)) - Decimal(str(previous_quote.adjusted_close)))), abs(float(Decimal(str(quote.high)) - Decimal(str(previous_quote.adjusted_close)))))
                else:
                    if previous_quote.adjusted_high is None:
                        raise Exception('Quotes with adjusted values should not have earlier quotes with unadjusted values.')
                    else:
                        return max( float(Decimal(str(quote.adjusted_high)) - Decimal(str(quote.adjusted_low))), abs(float(Decimal(str(quote.adjusted_low)) - Decimal(str(previous_quote.adjusted_close)))), abs(float(Decimal(str(quote.adjusted_high)) - Decimal(str(previous_quote.adjusted_close)))))
            else:
                if quote.adjusted_high is None:
                    return float(Decimal(str(quote.high)) - Decimal(str(quote.low)))
                else:
                    return float(Decimal(str(quote.adjusted_high)) - Decimal(str(quote.adjusted_low)))

class RiskRange():

# Calculates tradeable risk ranges for securities based on price, volume, and historic volatility

    pass
