import json

from datetime import datetime as dt
from types import SimpleNamespace

from olympus import Series
from olympus.securities import BUY, SELL
from olympus.securities.indicators import Math

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
        "Name": None,
        "Description": None
       }
}


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


class _Signal(SimpleNamespace):
    # Buy/sell signals
    # The internal "Signals" series is composed of these

    def __init__(self, date, signal_type, rule):
        super(_Signal, self).__init__()
        self.date = date
        self.type = signal_type
        self.rule = rule


class _Sequential():

    def __init__(self, date, setup_type):
        self.date = date
        self.type = setup_type
        self.dates = []
        self.dates.append(date)

    def add_date(self, date):
        self.dates.append(date)

    def complete(self, threshold):
        return self.count() == threshold

    def count(self):
        return len(self.dates)


class _Resistance():
    # A TD Setup Trend upper price extreme

    def __init__(self, date, price):
        self.date = date
        self.price = price


class _Support():
    # A TD Setup Trend lower price extreme

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
        self.setup = None
        self.countdown = None
        self.resistance = None
        self.support = None
        self.signals = Series()
        flip_lookback = price_series.lookback(LONG_LOOKBACK + 1)
        long_lookback = price_series.lookback(LONG_LOOKBACK)
        short_lookback = price_series.lookback(SHORT_LOOKBACK)
        previous_day = price_series.lookback(1)
        quote = price_series.next(reset=True)
        while quote is not None:
            (self.high, self.low, self.close) = self._which_price(quote)
            if flip_lookback is not None:
                # Must be able to look at least this far back
                # to initiate and manage chart points
                #
                # Check for Bearish or Bullish TD Price Flip
                #
                (flip_high, flip_low, flip_close) = self._which_price(
                        flip_lookback)
                (long_high, long_low, long_close) = self._which_price(
                        long_lookback)
                (short_high, short_low, short_close) = self._which_price(
                        short_lookback)
                (previous_high, previous_low, previous_close) = \
                    self._which_price(previous_day)
                #
                # A Bearish TD Price Flip occurs when the market records a
                # close greater than the close four bars earlier, immediately
                # followed by a close less than the close four bars earlier.
                #
                if (
                        previous_close > flip_close and
                        self.close < long_close):
                    self.setup = _Sequential(quote.date, BUY)
                #
                # A Bullish TD Price Flip occurs when the market records a
                # close less than the close four bars before, immediately
                # followed by a close greater than the close four bars earlier.
                #
                elif (
                        previous_close < flip_close and
                        self.close > long_close):
                    self.setup = _Sequential(quote.date, SELL)
                else:
                    if self.setup is not None:
                        if self.setup.type == BUY:
                            if self.close < long_close:
                                self.setup.add_date(quote.date)
                            else:
                                self.setup = None
                        else:  # SELL
                            if self.close > long_close:
                                self.setup.add_date(quote.date)
                            else:
                                self.setup = None
                        if self.setup.complete(self.formation_periods):
                            # TD Setup complete
                            self.setup = None
                    if self.countdown is not None:
                        if self.countdown.type == BUY:
                            pass  # ALEX self.array_periods
                        else:  # SELL
                            pass  # ALEX
                        if self.countdown.complete(self.array_periods):
                            # TD Countdown complete
                            self.countdown = None
            flip_lookback = price_series.lookback(LONG_LOOKBACK + 1)
            long_lookback = price_series.lookback(LONG_LOOKBACK)
            short_lookback = price_series.lookback(SHORT_LOOKBACK)
            previous_day = price_series.lookback(1)
            quote = price_series.next()

    def _add_meta(self, key, data):
        if not hasattr(self, 'meta'):
            self.meta = {}
        self.meta[key] = data

    def _which_price(self, quote):
        if self.as_traded is True or quote.adjusted_high is None:
            return quote.high, quote.low, quote.close
        return quote.adjusted_high, quote.adjusted_low, quote.adjusted_close
