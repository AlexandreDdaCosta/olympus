import json

from datetime import datetime as dt

DEFAULT_ATR_LENGTH = 20
DEFAULT_MOVING_AVERAGE_TYPE = 'Simple'
DEFAULT_MOVING_AVERAGE_LENGTH = 50
VALID_MOVING_AVERAGE_TYPES = ['Exponential', 'Simple']

class Indicators(object):

    def __init__(self,**kwargs):
        pass

    def average_true_range(self,price_series,**kwargs):
        print(json.dumps(price_series,indent=4))
        moving_average_type = kwargs.pop('moving_average_type', DEFAULT_MOVING_AVERAGE_TYPE)
        length = kwargs.pop('length', DEFAULT_ATR_LENGTH)
        use_as_traded_prices = kwargs.pop('use_as_traded_prices', False)
        parameters = { 'Length': length, 'MovingAverageType': moving_average_type }
        if use_as_traded_prices is False:
            parameters['UsingAsTradedPrices'] = 'No'
        else:
            parameters['UsingAsTradedPrices'] = 'Yes'
        atr = {}
        atr['Parameters'] = parameters
        atr['DateTimeSeries'] = {}
        return atr

    def moving_average(self,price_series,**kwargs):
        average_type = kwargs.pop('type', DEFAULT_MOVING_AVERAGE_TYPE)
        length = kwargs.pop('length', DEFAULT_MOVING_AVERAGE_LENGTH)
        use_as_traded_prices = kwargs.pop('use_as_traded_prices', False)
        parameters = { 'Length': length, 'Type': average_type }
        if use_as_traded_prices is False:
            parameters['UsingAsTradedPrices'] = 'No'
        else:
            parameters['UsingAsTradedPrices'] = 'Yes'
        ma = {}
        ma['Parameters'] = parameters
        ma['DateTimeSeries'] = {}
        return ma
