import json

# Chart intervals

INTERVALS = ('5min', 'daily', 'weekly', 'monthly')


class Interval(object):

    def __init__(self, start_datetime, quote):
        price_attributes = ('open',
                            'close',
                            'high',
                            'low',
                            'adjusted_open',
                            'adjusted_close',
                            'adjusted_high',
                            'adjusted_low')
        for attribute in price_attributes:
            if attribute in quote:
                setattr(self, attribute, quote[attribute])


class Chart(object):

    def __init__(self, interval):
        if interval not in INTERVALS:
            raise Exception('Invalid interval ' + str(interval))
