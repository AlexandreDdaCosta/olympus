import json

from datetime import datetime as dt

from olympus import Series
from olympus.securities.indicators import Math


class Sequential(Series):
    # TD Sequential

    DEFAULT_ARRAY_PERIODS = 13
    MINIMUM_ARRAY_PERIODS = 8
    MAXIMUM_ARRAY_PERIODS = 18
    DEFAULT_FORMATION_PERIODS = 9
    MINIMUM_FORMATION_PERIODS = 9
    MAXIMUM_FORMATION_PERIODS = 13

    def __init__(self, price_series, **kwargs):
        super(Sequential, self).__init__()
        self.math = Math()
        self.array_periods = int(kwargs.pop('array_periods',
                                            DEFAULT_ARRAY_PERIODS))
        if not self.math.ranged(
                self.array_period,
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
                self.formation_period,
                MINIMUM_FORMATION_PERIODS,
                MAXIMUM_FORMATION_PERIODS):
            raise Exception('Parameter for "formation_periods" (%s) is not '
                            'within the available range: %s to %s' %
                            (
                                self.formation_periods,
                                MINIMUM_FORMATION_PERIODS,
                                MAXIMUM_FORMATION_PERIODS)
                            )
        price_series.sort()
        quote = price_series.next(reset=True)
        while quote is not None:
            quote = price_series.next()
