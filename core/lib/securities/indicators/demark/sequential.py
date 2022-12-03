import json

from datetime import datetime as dt

from olympus import Series
from olympus.securities.indicators import Math

DEFAULT_ARRAY_PERIODS = 13
MINIMUM_ARRAY_PERIODS = 8
MAXIMUM_ARRAY_PERIODS = 18
DEFAULT_FORMATION_PERIODS = 9
MINIMUM_FORMATION_PERIODS = 9
MAXIMUM_FORMATION_PERIODS = 13
LONG_LOOKBACK = 4  # Periods
SHORT_LOOKBACK = 2  # Periods


class _Chart():

    def __init__(self):
        self.meta = {'Date': dt.now().astimezone()}
        self.dates = Series()
        self.buy_countdowns = Series()
        self.sell_countdowns = Series()
        self.buy_setups = Series()
        self.sell_setups = Series()
        self.buy_signals = Series()
        self.sell_signals = Series()
        self.current_countdown = None
        self.current_resistance = None
        self.current_setup = None
        self.current_support = None


class Sequential(_Chart):
    # TD Sequential

    def __init__(self, price_series, **kwargs):
        super(Sequential, self).__init__()
        self.math = Math()
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
        price_series.sort()
        quote = price_series.next(reset=True)
        while quote is not None:
            quote = price_series.next()
