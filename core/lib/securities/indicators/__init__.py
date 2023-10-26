# pyright: reportGeneralTypeIssues=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportOptionalOperand=false
# pyright: reportUnboundVariable=false

import math
import types

from decimal import Decimal

from olympus import Series

DEFAULT_ATR_PERIODS = 20
MINIMUM_ATR_PERIODS = 8
MAXIMUM_ATR_PERIODS = 50

DEFAULT_MOVING_AVERAGE_TYPE = 'Simple'
DEFAULT_MOVING_AVERAGE_PERIODS = 20
MINIMUM_MOVING_AVERAGE_PERIODS = 8
MAXIMUM_MOVING_AVERAGE_PERIODS = 200
VALID_MOVING_AVERAGE_TYPES = ['Simple', 'Exponential', 'Hull']

DEFAULT_STANDARD_DEVIATION = 2.0

PRICE_ROUNDER_ADJUSTED = 6
PRICE_ROUNDER_AS_TRADED = 2


class AverageTrueRange(Series):
    # Calculates periodic true range and average true range for a price series

    def __init__(self, price_series: list, **kwargs):
        super(AverageTrueRange, self).__init__()
        self.math = Math()
        periods = int(kwargs.pop('periods', DEFAULT_ATR_PERIODS))
        if periods < MINIMUM_ATR_PERIODS or periods > MAXIMUM_ATR_PERIODS:
            raise Exception('Parameter for "periods" (%s) is not within '
                            'the available range: %s to %s' %
                            (periods, MINIMUM_ATR_PERIODS, MAXIMUM_ATR_PERIODS)
                            )
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
            atr_entry.true_range = self.math.round(
                self._true_range(quote, previous_quote))
            atr_entry.true_range_adjusted = self.math.round(
                self._true_range(quote,
                                 previous_quote,
                                 True),
                PRICE_ROUNDER_ADJUSTED)
            if period <= periods:
                atr_sum += Decimal(str(atr_entry.true_range))
                atr_entry.atr = self.math.round(atr_sum / period)
                atr_sum_adjusted += Decimal(str(atr_entry.true_range_adjusted))
                atr_entry.atr_adjusted = self.math.round(
                    atr_sum_adjusted / period,
                    PRICE_ROUNDER_ADJUSTED)
                if period == periods:
                    last_atr = Decimal(atr_entry.atr)
                    last_atr_adjusted = Decimal(atr_entry.atr_adjusted)
                period = period + 1
            else:
                last_atr = (
                    (last_atr * (periods - 1)) +
                    Decimal(atr_entry.true_range)) / periods
                last_atr_adjusted = (
                    (last_atr_adjusted * (periods - 1)) +
                    Decimal(atr_entry.true_range_adjusted)) / periods
                atr_entry.atr = self.math.round(last_atr)
                atr_entry.atr_adjusted = self.math.round(
                    last_atr_adjusted,
                    PRICE_ROUNDER_ADJUSTED)
            self.add(atr_entry)
            previous_quote = quote
            quote = price_series.next()

    def _true_range(self,
                    quote: float,
                    previous_quote: float = None,
                    adjusted=False):
        if adjusted is False:
            if previous_quote is not None:
                return max(
                    Decimal(str(quote.high)) - Decimal(str(quote.low)),
                    abs(
                        Decimal(str(quote.low)) -
                        Decimal(str(previous_quote.close))
                    ),
                    abs(
                        Decimal(str(quote.high)) -
                        Decimal(str(previous_quote.close))
                    )
                )
            else:
                return Decimal(str(quote.high)) - Decimal(str(quote.low))
        else:
            if previous_quote is not None:
                if quote.adjusted_high is None:
                    if previous_quote.adjusted_high is None:
                        return max(
                            Decimal(str(quote.high)) -
                            Decimal(str(quote.low)),
                            abs(
                                Decimal(str(quote.low)) -
                                Decimal(str(previous_quote.close))
                            ),
                            abs(
                                Decimal(str(quote.high)) -
                                Decimal(str(previous_quote.close))
                            )
                        )
                    else:
                        return max(
                            Decimal(str(quote.high)) -
                            Decimal(str(quote.low)),
                            abs(
                                Decimal(str(quote.low)) -
                                Decimal(str(previous_quote.adjusted_close))
                            ),
                            abs(
                                Decimal(str(quote.high)) -
                                Decimal(str(previous_quote.adjusted_close))
                            )
                        )
                else:
                    if previous_quote.adjusted_high is None:
                        raise Exception('Quotes with adjusted values should '
                                        'not have earlier quotes with '
                                        'unadjusted values.')
                    else:
                        return max(
                            Decimal(str(quote.adjusted_high)) -
                            Decimal(str(quote.adjusted_low)),
                            abs(
                                Decimal(str(quote.adjusted_low)) -
                                Decimal(str(previous_quote.adjusted_close))
                            ),
                            abs(
                                Decimal(str(quote.adjusted_high)) -
                                Decimal(str(previous_quote.adjusted_close))
                            )
                        )
            else:
                if quote.adjusted_high is None:
                    return Decimal(str(quote.high)) - Decimal(str(quote.low))
                else:
                    return (
                        Decimal(str(quote.adjusted_high)) -
                        Decimal(str(quote.adjusted_low))
                    )


class MovingAverage(Series):
    # Calculates various periodic moving average types for a price series

    def __init__(self, price_series: list, **kwargs):
        super(MovingAverage, self).__init__()
        self.math = Math()
        average_type = kwargs.pop('average_type', DEFAULT_MOVING_AVERAGE_TYPE)
        periods = int(kwargs.pop('periods', DEFAULT_MOVING_AVERAGE_PERIODS))
        if (
                periods < MINIMUM_MOVING_AVERAGE_PERIODS or
                periods > MAXIMUM_MOVING_AVERAGE_PERIODS):
            raise Exception('Parameter for "periods" (%s) is not within '
                            'the available range: %s to %s'
                            % (
                                periods,
                                MINIMUM_MOVING_AVERAGE_PERIODS,
                                MAXIMUM_MOVING_AVERAGE_PERIODS)
                            )
        if average_type not in VALID_MOVING_AVERAGE_TYPES:
            raise Exception('Parameter for "average_type" (%s) is invalid; '
                            'choose from the following: %s'
                            % (
                                average_type,
                                ', '.join(VALID_MOVING_AVERAGE_TYPES)
                            )
                            )
        price_series.sort()
        try:
            func = getattr(self, '_' + average_type.lower())
        except AttributeError:
            raise Exception('Function for average "%s" not found.'
                            % (average_type)
                            )
        else:
            func(price_series, periods)

    def _exponential(self, price_series: list, periods: int):
        price_series.sort()
        k = Decimal(2 / (periods + 1))  # Weighting factor for EMA
        divisor = 0
        period = 1
        previous_ema = 0.0
        previous_ema_adjusted = 0.0
        quotes_totals = 0
        quotes_adjusted_totals = 0
        quote = price_series.next(reset=True)
        while quote is not None:
            ma_entry = types.SimpleNamespace()
            ma_entry.date = quote.date
            if period <= periods:
                divisor = divisor + 1
                quotes_totals = quotes_totals + quote.close
                if quote.adjusted_close is not None:
                    quotes_adjusted_totals += quote.adjusted_close
                else:
                    quotes_adjusted_totals += quote.close
                ma_entry.moving_average = self.math.round(
                    quotes_totals / divisor)
                ma_entry.moving_average_adjusted = self.math.round(
                    quotes_adjusted_totals / divisor,
                    PRICE_ROUNDER_ADJUSTED)
                period = period + 1
            else:
                # EMA = k * (current price - previous EMA) + previous EMA
                ma_entry.moving_average = self.math.round(
                    (k * (Decimal(str(quote.close)) - previous_ema)) +
                    previous_ema)
                if quote.adjusted_close is not None:
                    ma_entry.moving_average_adjusted = self.math.round(
                        (
                            k * (
                                Decimal(str(quote.adjusted_close)) -
                                previous_ema_adjusted
                            )
                        ) +
                        previous_ema_adjusted,
                        PRICE_ROUNDER_ADJUSTED)
                else:
                    ma_entry.moving_average_adjusted = self.math.round(
                        (
                            k * (
                                Decimal(str(quote.close)) -
                                previous_ema_adjusted
                            )
                        ) + previous_ema_adjusted,
                        PRICE_ROUNDER_ADJUSTED)
            previous_ema = Decimal(str(ma_entry.moving_average))
            previous_ema_adjusted = Decimal(
                str(ma_entry.moving_average_adjusted))
            self.add(ma_entry)
            quote = price_series.next()

    def _hull(self, price_series: list, periods: int):
        price_series.sort()
        lower_index = 0
        smoothing_periods = round(math.sqrt(periods))
        smoothing_summation = 1
        period = 1
        quotes = []
        quotes_adjusted = []
        quote = price_series.next(reset=True)
        smoothing_period = 1
        summation = 0
        upper_index = 1
        wma = []
        wma_adjusted = []
        while quote is not None:
            quotes.append(quote.close)
            if quote.adjusted_close is not None:
                quotes_adjusted.append(quote.adjusted_close)
            else:
                quotes_adjusted.append(quote.close)
            if period <= periods:
                summation = summation + period
                half_summation = 0
                half_summation_periods = math.ceil(len(quotes) / 2)
                while half_summation_periods > 0:
                    half_summation = half_summation + half_summation_periods
                    half_summation_periods = half_summation_periods - 1
                period = period + 1
            else:
                quotes.pop(0)
                quotes_adjusted.pop(0)
            wma1 = self._weighted(
                quotes,
                math.ceil(len(quotes) / 2),
                half_summation)
            wma1_adjusted = self._weighted(
                quotes_adjusted,
                math.ceil(len(quotes_adjusted) / 2),
                half_summation,
                PRICE_ROUNDER_ADJUSTED)
            wma2 = self._weighted(quotes, len(quotes), summation)
            wma2_adjusted = self._weighted(
                quotes_adjusted,
                len(quotes_adjusted),
                summation,
                PRICE_ROUNDER_ADJUSTED)
            wma_value = (2 * wma1) - wma2
            wma.append(wma_value)
            wma_value_adjusted = (2 * wma1_adjusted) - wma2_adjusted
            wma_adjusted.append(wma_value_adjusted)
            ma_entry = types.SimpleNamespace()
            ma_entry.date = quote.date
            ma_entry.moving_average = self._weighted(
                wma[lower_index:upper_index],
                smoothing_period,
                smoothing_summation)
            ma_entry.moving_average_adjusted = self._weighted(
                wma_adjusted[lower_index:upper_index],
                smoothing_period,
                smoothing_summation,
                PRICE_ROUNDER_ADJUSTED)
            self.add(ma_entry)
            if smoothing_period < smoothing_periods:
                smoothing_period = smoothing_period + 1
                smoothing_summation = smoothing_summation + smoothing_period
            else:
                lower_index = lower_index + 1
            upper_index = upper_index + 1
            quote = price_series.next()

    def _weighted(self,
                  price_array: list,
                  periods: int,
                  summation: int,
                  rounding_factor: int = PRICE_ROUNDER_AS_TRADED) -> float:
        average = 0.0
        for price in reversed(price_array):
            average = average + ((price * periods) / summation)
            periods = periods - 1
            if periods == 0:
                break
        return self.math.round(average, rounding_factor)

    def _simple(self, price_series: list, periods: int):
        price_series.sort()
        quote = price_series.next(reset=True)
        divisor = 0
        period = 1
        quotes = []
        quotes_totals = 0
        quotes_adjusted = []
        quotes_adjusted_totals = 0
        while quote is not None:
            ma_entry = types.SimpleNamespace()
            ma_entry.date = quote.date
            if period <= periods:
                divisor = divisor + 1
                period = period + 1
            else:
                quotes_totals -= quotes.pop(0)
                quotes_adjusted_totals -= quotes_adjusted.pop(0)
            quotes.append(quote.close)
            quotes_totals = quotes_totals + quote.close
            ma_entry.moving_average = self.math.round(quotes_totals / divisor)
            if quote.adjusted_close is not None:
                quotes_adjusted.append(quote.adjusted_close)
                quotes_adjusted_totals += quote.adjusted_close
            else:
                quotes_adjusted.append(quote.close)
                quotes_adjusted_totals = quotes_adjusted_totals + quote.close
            ma_entry.moving_average_adjusted = self.math.round(
                quotes_adjusted_totals / divisor,
                PRICE_ROUNDER_ADJUSTED)
            self.add(ma_entry)
            quote = price_series.next()


class BollingerBands(MovingAverage):
    # Calculates Bollinger Bands, which are designed to give traders a higher
    # probability of identifying when an asset is oversold or overbought.

    def __init__(self, price_series: list, **kwargs):
        periods = int(kwargs.get('periods', DEFAULT_MOVING_AVERAGE_PERIODS))
        standard_deviation = float(kwargs.get('standard_deviation',
                                              DEFAULT_STANDARD_DEVIATION))
        super(BollingerBands, self).__init__(price_series, **kwargs)
        # At this point the moving average has been calculated.
        # Next we move through the price series and associated moving averages
        # and calculate the bands themselves.
        price_series.sort()
        quote = price_series.next(reset=True)
        index = 0
        ma = self.next(reset=True)
        divisor = 0
        quotes = []
        quotes_precalculation = []
        quotes_std_dev = 0
        quotes_adjusted = []
        quotes_adjusted_precalculation = []
        quotes_adjusted_std_dev = 0
        while quote is not None:
            if divisor < periods:
                divisor = divisor + 1
            else:
                quotes.pop(0)
                quotes_precalculation.pop(0)
                quotes_adjusted.pop(0)
                quotes_adjusted_precalculation.pop(0)
            quotes.append(quote.close)
            quotes_precalculation.append(
                pow((quote.close - ma.moving_average), 2))
            quotes_std_dev = math.sqrt(
                sum(quotes_precalculation) / divisor)
            if quote.adjusted_close is not None:
                quotes_adjusted.append(quote.adjusted_close)
                quotes_adjusted_precalculation.append(
                    pow((quote.adjusted_close -
                         ma.moving_average_adjusted), 2))
            else:
                quotes_adjusted.append(quote.close)
                quotes_adjusted_precalculation.append(
                    pow((quote.close -
                         ma.moving_average), 2))
            quotes_adjusted_std_dev = math.sqrt(
                sum(quotes_adjusted_precalculation) / divisor)
            extension = {}
            deviation = quotes_std_dev * standard_deviation
            extension['lower_band'] = ma.moving_average - deviation
            extension['upper_band'] = ma.moving_average + deviation
            adjusted_deviation = quotes_adjusted_std_dev * standard_deviation
            extension['lower_band_adjusted'] = \
                ma.moving_average_adjusted - adjusted_deviation
            extension['upper_band_adjusted'] = \
                ma.moving_average_adjusted + adjusted_deviation
            self.extend(index, extension)
            quote = price_series.next()
            index += 1
            ma = self.next()


class RiskRange():
    # Calculates tradeable risk ranges for securities based on
    # price, volume, and historic volatility
    pass


class Math():
    # Common math operations with indicators

    def ranged(self,
               value: float,
               low_end: float,
               high_end: float):
        if float(value) < low_end or float(value) > high_end:
            return False
        return True

    def round(self,
              value: float,
              rounding_factor: int = PRICE_ROUNDER_AS_TRADED) -> float:
        return round(float(value), rounding_factor)
