import json

from datetime import datetime as dt

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

'''
-----
RULES
-----

List of rules that apply to buy and sell signals:

1. Bearish TD Price Flip.
   When the market records a close greater than the close four bars earlier,
   immediately followed by a close less than the close four bars earlier
2. Bullish TD Price Flip.
   When the market records a close less than the close four bars earlier,
   immediately followed by a close greater than the close four bars earlier

'''


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


class _Signal():
    # Buy/sell signals

    def __init__(self, date, signal_type, rule):
        self.date = date
        self.signal_type = signal_type


class _Countdown():

    def __init__(self, date):
        self.date = date


class _Setup():

    def __init__(self, date):
        self.date = date


class _Resistance():
    # A TD Setup Trend upper price extreme

    def __init__(self, date):
        self.date = date


class _Support():
    # A TD Setup Trend lower price extreme

    def __init__(self, date):
        self.date = date


class Sequential(Series):
    # TD Sequential

    def __init__(self, price_series, **kwargs):
        super(Sequential, self).__init__()
        self.math = Math()
        self.meta = {'Date': dt.now().astimezone()}
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
        self._chartpoints(price_series)

    def _chartpoints(self, price_series):
        self.setup = None
        self.countdown = None
        self.resistance = None
        self.support = None
        self.signals = Series()
        price_series.sort()
        long_lookback = price_series.lookback(LONG_LOOKBACK)
        short_lookback = price_series.lookback(SHORT_LOOKBACK)
        quote = price_series.next(reset=True)
        while quote is not None:
            if self.have_items() is False:
                # No date entries yet
                pass
            else:
                pass
            long_lookback = price_series.lookback(LONG_LOOKBACK)
            short_lookback = price_series.lookback(SHORT_LOOKBACK)
            quote = price_series.next()
