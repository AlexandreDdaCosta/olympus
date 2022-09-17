# Recognized quote attributes

# These attributes are grouped under "adjusted" in a "Quote" object.
# Typically they reference equity prices, in which past as-traded prices and volumes
# can be adjusted for dividends and splits.
MAP_ADJUSTED_QUOTE_ATTRIBUTES = {
    "Adjusted Close": "close",
    "Adjusted High": "high",
    "Adjusted Low": "low",
    "Adjusted Open": "open",
    "Adjusted Volume": "volume"
    }
# These attributes are grouped under "misc" in a "Quote" object. None are required.
MAP_MISCELLANEOUS_QUOTE_ATTRIBUTES = {
    }
# All quotes in a series must have these attributes
MAP_STANDARD_QUOTE_ATTRIBUTES = {
    "Close": "close", 
    "DateTime": "datetime", 
    "High": "high",
    "Low": "low", 
    "Open": "open",
    "Volume": "volume"
    }

# Standardized quote format objects for all securities.
# These are intended for quotes in a series.

class Quote(object):

    def __init__(self,data):
        if type(data) != dict:
            raise Exception('For the "Quote" object, parameter "data" must be a dict.')

class QuoteSeries(object):
    '''
A time-ordered list of quote objects
    '''

    def __init__(self,quote_series=None,**kwargs):
        if type(quote_series) != list:
            raise Exception('Parameter "quote_series" must be a list.')
        raw_data = kwargs.pop('raw_data',False)
        reverse_datetime_order = kwargs.pop('reverse_datetime_order',False)
        self.iterator_index = 0
        self.quotes = []
        for quote in quote_series:
            if raw_data is True:
                # quote_series is a list of dicts
                quote_object = Quote(quote)
                self.quotes.append(quote_object)
            else:
                # quote_series is a list of quote objects
                if isinstance(quote, Quote) is False:
                    raise Exception('Without the "raw_data" setting, all items in quote_series must be of the "Quote" class.')
                self.quotes.append(quote)
        if self.quotes:
            self.quotes = sorted(self.quotes, key=lambda l: (l.datetime), reverse=reverse_datetime_order)

    def first(self):
        # First quote in time ordered series
        if not self.quotes:
            return None
        return self.quotes[0]

    def last(self):
        # Last quote in time ordered series
        if not self.quotes:
            return None
        return self.quotes[-1]

    def next(self,**kwargs):
        # Used to iterate through a series of quotes
        if not self.quotes:
            return None
        reset = kwargs.pop('reset',False)
        if reset is True:
            self.iterator_index = 0
        try:
            quote = self.quotes[self.iterator_index]
        except IndexError:
            return False
        self.iterator_index = self.iterator_index + 1
        return quote
