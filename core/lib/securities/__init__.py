from olympus import String

# The attributes that all securities must have
SECURITY_STANDARD_ATTRIBUTES = [ "Name", "SecurityClass", "Symbol" ]

# The attributes that all price quotes must have
PRICE_STANDARD_ATTRIBUTES = [ "Close", "DateTime", "High", "Low", "Open", "Volume" ]

# The attributes that all quote adjustments must have
PRICE_ADJUSTED_ATTRIBUTES = [ "Adjusted Close", "Adjusted High", "Adjusted Low", "Adjusted Open", "Adjusted Volume" ]
MAP_ADJUSTED_ATTRIBUTES = {
    "Adjusted Close": "close",
    "Adjusted High": "high",
    "Adjusted Low": "low",
    "Adjusted Open": "open",
    "Adjusted Volume": "volume"
}

class _ClassMisc(object):

    def __init__(self,named_attributes=None):
        self.misc_attributes = None
        self.named_attributes = named_attributes

    def add(self,misc_name,misc_value):
        string = String()
        misc_name = string.pascal_case_to_underscore(misc_name)
        if self.named_attributes is not None:
            if misc_name in self.named_attributes:
                raise Exception('Miscellaneous quote data ' + str(misc_name) + ' exists as a named attribute and cannot be miscellaneous data.')
        if self.misc_attributes is None:
            self.misc_attributes = []
        setattr(self,misc_name,misc_value)
        self.misc_attributes.append(misc_name)

    def get(self,misc_name):
        if self.misc_attributes is not None and misc_name in self.misc_attributes:
            return getattr(self, misc_name)
        return None

    def list(self):
        return sorted(self.misc_attributes)

class _ValidateAttributes(object):

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

class AttributeGetter(object):

    def __init__(self):
        pass

    def get_price_standard_attributes(self):
        attributes = []
        string = String()
        for attribute in PRICE_STANDARD_ATTRIBUTES:
            attributes.append(string.pascal_case_to_underscore(attribute))
        return sorted(attributes)

    def get_security_standard_attributes(self):
        attributes = []
        string = String()
        for attribute in SECURITY_STANDARD_ATTRIBUTES:
            attributes.append(string.pascal_case_to_underscore(attribute))
        return sorted(attributes)

class QuoteAdjustments(object):

    # Typically these attributes reference equity prices, in which past as-traded prices and volumes can be adjusted for dividends and splits.

    def __init__(self,adjustments):
        validator = _ValidateAttributes(adjustments,PRICE_ADJUSTED_ATTRIBUTES,'adjusted details')
        self.adjusted_attributes = []
        for adjustment in adjustments:
            setattr(self,MAP_ADJUSTED_ATTRIBUTES[adjustment],adjustments[adjustment])
            self.adjusted_attributes.append(MAP_ADJUSTED_ATTRIBUTES[adjustment])

    def get(self,adjustment_name):
        if adjustment_name in self.adjusted_attributes:
            return getattr(self,name)
        return None

    def list(self):
        return sorted(self.adjusted_attributes)

class Quote(object):

    def __init__(self,quote):
        self.adjustments = None
        self.misc = None
        self.standard_attributes = []
        validator = _ValidateAttributes(quote,PRICE_STANDARD_ATTRIBUTES,'standard details')
        string = String()
        for detail in quote:
            uc_detail = string.pascal_case_to_underscore(detail)
            setattr(self,uc_detail,quote[detail])
            self.standard_attributes.append(uc_detail)

    def add_adjustments(self,adjustments):
        self.adjustments = QuoteAdjustments(adjustments)

    def add(self,misc_name,misc_value):
        # Will overwrite an existing attribute
        if self.misc is None:
            self.misc = _ClassMisc(named_attributes=PRICE_ADJUSTED_ATTRIBUTES + PRICE_STANDARD_ATTRIBUTES)
        self.misc.add(misc_name,misc_value)

    def add_symbol(self,symbol):
        # For those cases in which the symbol itself needs to be part of a quote
        self.symbol = symbol.upper()

    def get(self,name):
        if name in self.standard_attributes:
            return getattr(self,name)
        if self.adjustments is not None:
            if name in self.adjustments.list():
                return self.adjustments.get(name)
        if self.misc is not None:
            return self.misc.get(name)
        return None

    def list(self):
        listed = []
        if self.misc is not None:
            listed = listed + self.misc.list()
        if self.adjustments is not None:
            listed = listed + self.adjustments.list()
        return sorted(listed + self.standard_attributes)

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

class Security(object):

    def __init__(self,standard_data):
        self.misc = None
        self.standard_attributes = []
        validator = _ValidateAttributes(standard_data,SECURITY_STANDARD_ATTRIBUTES,'standard security details')
        string = String()
        for detail in standard_data:
            uc_detail = string.pascal_case_to_underscore(detail)
            setattr(self,uc_detail,standard_data[detail])
            self.standard_attributes.append(uc_detail)

    def add(self,misc_name,misc_value):
        # Will override an existing attribute
        if self.misc is None:
            self.misc = _ClassMisc(named_attributes=SECURITY_STANDARD_ATTRIBUTES)
        self.misc.add(misc_name,misc_value)

    def get(self,name):
        if name in self.standard_attributes:
            return getattr(self,name)
        if self.misc is not None:
            return self.misc.get(name)
        return None

    def list(self):
        if self.misc is None:
            return sorted(self.standard_attributes)
        return sorted(self.misc.list() + self.standard_attributes)
