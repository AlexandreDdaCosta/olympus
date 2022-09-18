# The attributes that all price quotes must have
PRICE_STANDARD_ATTRIBUTES = [ "Close", "DateTime", "High", "Low", "Open", "Volume" ]

# The attributes that all quote adjustments must have
PRICE_ADJUSTED_ATTRIBUTES = [ "Adjusted Close", "Adjusted High", "Adjusted Low", "Adjusted Open", "Adjusted Volume" ]

class ValidateQuoteKeys(object):

    def __init__(self,quote,attribute_list,attribute_type):
        if not isinstance(quote, dict):
            raise Exception('Quote details must be a dict.')
        bad_attributes = []
        for attribute in quote:
            if attribute not in attribute_list:
                bad_attributes.append(attribute)
        if bad_attributes:
            raise Exception('Invalid keys in ' + attribute_type + ': ' + ', ' . join(bad_attributes))
        missing_attributes = []
        for key in attribute_list:
            if key not in quote:
                missing_attributes.append(key)
        if missing_attributes:
            raise Exception('Keys in ' + attribute_type + ' are incomplete: ' + ', ' . join(missing_attributes))

# Standardized quote format objects for all securities.
# These are intended for quotes in a series.

class QuoteAdjustments(object):

    # Typically these attributes  reference equity prices, in which past as-traded prices and volumes can be adjusted for dividends and splits.
    MAP_ADJUSTED_ATTRIBUTES = {
        "Adjusted Close": "close",
        "Adjusted High": "high",
        "Adjusted Low": "low",
        "Adjusted Open": "open",
        "Adjusted Volume": "volume"
    }

    def __init__(self,adjustments):
        validator = ValidateQuoteKeys(adjustments,PRICE_ADJUSTED_ATTRIBUTES,'adjusted details')
        for adjustment in adjustments:
            setattr(self,self.MAP_ADJUSTED_ATTRIBUTES[adjustment],adjustments[adjustment])

class QuoteMisc(object):

    def __init__(self):
        pass

    def add_misc(self,misc_name,misc_value):
        if misc_name in PRICE_STANDARD_ATTRIBUTES or misc_name in PRICE_ADJUSTED_ATTRIBUTES:
            raise Exception('Miscellaneous quote data ' + str(misc_name) + ' exists as a named attribute and cannot be miscellanoues data.')
        setattr(self,misc_name,misc_value)

class Quote(object):

    MAP_STANDARD_ATTRIBUTES = {
        "Close": "close", 
        "DateTime": "datetime", 
        "High": "high",
        "Low": "low", 
        "Open": "open",
        "Volume": "volume"
    }

    def __init__(self,quote):
        self.adjustments = None
        self.misc = None
        validator = ValidateQuoteKeys(quote,PRICE_STANDARD_ATTRIBUTES,'standard details')
        for detail in quote:
            setattr(self,self.MAP_STANDARD_ATTRIBUTES[detail],quote[detail])

    def add_adjustments(self,adjustments):
        self.adjustments = QuoteAdjustments(adjustments)

    def add_misc(self,misc_name,misc_value):
        if self.misc is None:
            self.misc = QuoteMisc()
        self.misc.add_misc(misc_name,misc_value)

    def add_symbol(self,symbol):
        # For those cases in which the symbol itself needs to be part of a quote
        self.symbol = symbol.upper()

class QuoteSeries(object):
    '''
A time-ordered list of quote objects
    '''

    def __init__(self,quote_series=None,**kwargs):
        if not isinstance(quote_series, list):
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
