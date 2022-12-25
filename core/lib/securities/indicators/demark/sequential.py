import json

from datetime import datetime as dt
from types import SimpleNamespace

from olympus import Series
from olympus.securities import BUY, SELL
from olympus.securities.indicators import Math

# Adjustable settings and their limits
DEFAULT_ARRAY_PERIODS = 13
MINIMUM_ARRAY_PERIODS = 8
MAXIMUM_ARRAY_PERIODS = 18
DEFAULT_FORMATION_PERIODS = 9
MINIMUM_FORMATION_PERIODS = 9
MAXIMUM_FORMATION_PERIODS = 13
LONG_LOOKBACK = 4  # Periods
SHORT_LOOKBACK = 2  # Periods

# List of rules that apply to buy and sell signals:
RULES = {
    1: {
        "Name": "Bearish TD Price Flip",
        "Description": "A Bearish TD Price Flip occurs when the market "
                       "records a close greater than the close four bars "
                       "earlier, immediately followed by a close less than "
                       "the close four bars earlier."
       },
    2: {
        "Name": "Bullish TD Price Flip",
        "Description": "A Bullish TD Price Flip occurs when the market "
                       "records a close less than the close four bars before, "
                       "immediately followed by a close greater than the "
                       "close four bars earlier."
       },
    3: {
        "Name": None,
        "Description": None
       }
}

# Miscellaneous
BULL_BEAR_TYPES = [BUY, SELL]


class _Date():
    # A Sequential() series is composed of these

    def __init__(self, date):
        self.date = date

    def add_countdown_step(self, step_number):
        pass

    def add_setup_step(self, step_number):
        pass

    def add_resistance_level(self, level):
        pass

    def add_support_level(self, level):
        pass

    def add_signal(self, signal_type, rule):
        pass


class _DateAggregator(SimpleNamespace):

    def __init__(self, price_series):
        super(_DateAggregator, self).__init__()
        self.flip_lookback = price_series.lookback(LONG_LOOKBACK + 1)
        self.long_lookback = price_series.lookback(LONG_LOOKBACK)
        self.short_lookback = price_series.lookback(SHORT_LOOKBACK)
        self.previous_day = price_series.lookback(1)


class _PriceFlip(SimpleNamespace):

    def __init__(self, flip_type, quotes):
        super(_PriceFlip, self).__init__()
        self.type = flip_type
        if self.type == BUY:
            self.rule = RULES[1]
        else:  # SELL
            self.rule = RULES[2]


class _Sequential():

    def __init__(self, date, sequence_type, aggregator):
        self.date = date
        self.dates = []
        self.dates.append(date)
        if sequence_type not in BULL_BEAR_TYPES:
            raise Exception('Bad value for sequence_type.')
        self.price_flip = _PriceFlip(sequence_type, aggregator)
        self.type = self.price_flip.type

    def add_date(self, date):
        self.dates.append(date)

    def complete(self, threshold):
        return self.count() == threshold

    def count(self):
        return len(self.dates)


class _Signal(SimpleNamespace):
    # Buy/sell signals
    # The internal "Signals" series is composed of these

    def __init__(self, date, signal_type, rule):
        super(_Signal, self).__init__()
        self.date = date
        self.type = signal_type
        self.rule = rule


class _Support():
    # A TD Setup Trend lower price extreme

    def __init__(self, date, price):
        self.date = date
        self.price = price


class _Resistance():
    # A TD Setup Trend upper price extreme

    def __init__(self, date, price):
        self.date = date
        self.price = price


class Sequential(Series):
    # TD Sequential

    def __init__(self, price_series, **kwargs):
        super(Sequential, self).__init__()
        self.math = Math()
        self._add_meta('Date', dt.now().astimezone())
        self.array_periods = int(kwargs.pop('array_periods',
                                            DEFAULT_ARRAY_PERIODS))
        if not self.math.ranged(
                self.array_periods,
                MINIMUM_ARRAY_PERIODS,
                MAXIMUM_ARRAY_PERIODS):
            raise Exception('Parameter for "array_periods" (%s) is not within '
                            'the available range: %s to %s' %
                            (
                                self.array_periods,
                                MINIMUM_ARRAY_PERIODS,
                                MAXIMUM_ARRAY_PERIODS)
                            )
        self._add_meta('Array Periods', self.array_periods)
        self.formation_periods = int(kwargs.pop('formation_periods',
                                                DEFAULT_FORMATION_PERIODS))
        if not self.math.ranged(
                self.formation_periods,
                MINIMUM_FORMATION_PERIODS,
                MAXIMUM_FORMATION_PERIODS):
            raise Exception('Parameter for "formation_periods" (%s) is not '
                            'within the available range: %s to %s' %
                            (
                                self.formation_periods,
                                MINIMUM_FORMATION_PERIODS,
                                MAXIMUM_FORMATION_PERIODS)
                            )
        self._add_meta('Formation Periods', self.formation_periods)
        self.as_traded = kwargs.pop('as_traded', False)
        if self.as_traded is True:
            self._add_meta('Price', 'As Traded')
        else:
            self._add_meta('Price', 'Adjusted')
        price_series.sort()
        self._add_meta('Start Date', price_series.first().date)
        self._add_meta('End Date', price_series.last().date)
        self._chartpoints(price_series)

    def _chartpoints(self, price_series):
        # Main internal function that creates the sequential chart
        self.cancelled_setups = []
        self.setup = None
        self.countdown = None
        self.resistance = None
        self.support = None
        self.signals = Series()
        aggregator = _DateAggregator(price_series)
        quote = price_series.next(reset=True)
        while quote is not None:
            (self.high, self.low, self.close) = self._which_price(quote)
            if aggregator.flip_lookback is not None:
                # Must be able to look at least this far back
                # to initiate and manage chart points
                #
                # Check for Bearish or Bullish TD Price Flip
                #
                (flip_high, flip_low, flip_close) = \
                    self._which_price(aggregator.flip_lookback)
                (long_high, long_low, long_close) = \
                    self._which_price(aggregator.long_lookback)
                (short_high, short_low, short_close) = \
                    self._which_price(aggregator.short_lookback)
                (previous_high, previous_low, previous_close) = \
                    self._which_price(aggregator.previous_day)
                # Bearish TD Price Flip
                if (
                        previous_close > flip_close and
                        self.close < long_close):
                    if self.setup is not None:
                        self.cancelled_setups.append(self.setup)
                    self.setup = _Sequential(quote.date, BUY, aggregator)
                # Bullish TD Price Flip
                elif (
                        previous_close < flip_close and
                        self.close > long_close):
                    if self.setup is not None:
                        self.cancelled_setups.append(self.setup)
                    self.setup = _Sequential(quote.date, SELL, aggregator)
                else:
                    if self.setup is not None:
                        if self.setup.type == BUY:
                            if self.close < long_close:
                                self.setup.add_date(aggregator)
                            else:
                                self.cancelled_setups.append(self.setup)
                                self.setup = None
                        else:  # SELL
                            if self.close > long_close:
                                self.setup.add_date(aggregator)
                            else:
                                self.cancelled_setups.append(self.setup)
                                self.setup = None
                        if self.setup.complete(self.formation_periods):
                            # TD Setup complete
                            # Write out data to individual dates
                            # ALEX
                            self.setup = None
                    '''
                    if self.countdown is not None:
                        if self.countdown.type == BUY:
                            pass  # ALEX self.array_periods
                        else:  # SELL
                            pass  # ALEX
                        if self.countdown.complete(self.array_periods):
                            # TD Countdown complete
                            self.countdown = None
                    '''
            aggregator = _DateAggregator(price_series)
            quote = price_series.next()

    def _add_meta(self, key, data):
        if not hasattr(self, 'meta'):
            self.meta = {}
        self.meta[key] = data

    def _which_price(self, quote):
        if self.as_traded is True or quote.adjusted_high is None:
            return quote.high, quote.low, quote.close
        return quote.adjusted_high, quote.adjusted_low, quote.adjusted_close
