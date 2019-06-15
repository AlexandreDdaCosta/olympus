import json

class Sequence(object):

    def __init__(self,**kwargs):
        self.shares = 0
        self.cost = 0.00
        self.net = 0.00
        self.proceeds = 0.00
        self.unrealized_amount = 0.00
        self.largest_positive_unrealized = 0.00
        self.largest_negative_unrealized = 0.00

    def date(self,signal,**kwargs):
        # Trade BUY/SELL signals based on different algorithms
        pass
