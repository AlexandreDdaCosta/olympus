# pyright: reportGeneralTypeIssues=false
# pyright: reportOptionalMemberAccess=false

from olympus import Series, String

# The attributes that all price quotes must have
PRICE_STANDARD_ATTRIBUTES = [
    "Close",
    "DateTime",
    "High",
    "Low",
    "Open",
    "Volume"]

# The attributes that all quote adjustments must have
PRICE_ADJUSTED_ATTRIBUTES = [
    "Adjusted Close",
    "Adjusted High",
    "Adjusted Low",
    "Adjusted Open",
    "Adjusted Volume"]
MAP_ADJUSTED_ATTRIBUTES = {
    "Adjusted Close": "close",
    "Adjusted High": "high",
    "Adjusted Low": "low",
    "Adjusted Open": "open",
    "Adjusted Volume": "volume"}

# Signals and positioning

BUY = 'Buy'
SELL = 'Sell'


class _ClassMisc():

    def __init__(self, named_attributes=None):
        self.misc_attributes = None
        self.named_attributes = named_attributes

    def add(self, misc_name, misc_value):
        string = String()
        misc_name = string.pascal_case_to_underscore(misc_name)
        if self.named_attributes is not None:
            if misc_name in self.named_attributes:
                raise Exception('Miscellaneous quote data ' +
                                str(misc_name) +
                                ' exists as a named attribute and cannot '
                                'be miscellaneous data.')
        if self.misc_attributes is None:
            self.misc_attributes = []
        setattr(self, misc_name, misc_value)
        self.misc_attributes.append(misc_name)

    def get(self, misc_name):
        if (
                self.misc_attributes is not None and
                misc_name in self.misc_attributes):
            return getattr(self, misc_name)
        return None

    def list(self):
        return sorted(self.misc_attributes)


class _ValidateAttributes():

    def __init__(self, quote, attribute_list, attribute_type):
        if not isinstance(quote, dict):
            raise Exception('Quote details must be a dict.')
        bad_attributes = []
        for attribute in quote:
            if attribute not in attribute_list:
                bad_attributes.append(attribute)
        if bad_attributes:
            raise Exception('Invalid keys in ' +
                            attribute_type +
                            ': ' + ', ' . join(bad_attributes))
        missing_attributes = []
        for key in attribute_list:
            if key not in quote:
                missing_attributes.append(key)
        if missing_attributes:
            raise Exception('Keys in ' +
                            attribute_type +
                            ' are incomplete: ' +
                            ', ' . join(missing_attributes))


class QuoteAdjustments():
    # Typically these attributes reference equity prices, in which past
    # as-traded prices and volumes can be adjusted for dividends and splits.

    def __init__(self, adjustments):
        _ValidateAttributes(
            adjustments,
            PRICE_ADJUSTED_ATTRIBUTES,
            'adjusted details')
        self.adjusted_attributes = []
        for adjustment in adjustments:
            setattr(
                self,
                MAP_ADJUSTED_ATTRIBUTES[adjustment],
                adjustments[adjustment])
            self.adjusted_attributes.append(
                MAP_ADJUSTED_ATTRIBUTES[adjustment])

    def get(self, adjustment_name):
        if adjustment_name in self.adjusted_attributes:
            return getattr(self, adjustment_name)
        return None

    def list(self):
        return sorted(self.adjusted_attributes)


class Quote():

    def __init__(self, quote):
        self.adjustments = None
        self.misc = None
        self.standard_attributes = []
        _ValidateAttributes(
            quote,
            PRICE_STANDARD_ATTRIBUTES,
            'standard details')
        string = String()
        for detail in quote:
            uc_detail = string.pascal_case_to_underscore(detail)
            setattr(self, uc_detail, quote[detail])
            self.standard_attributes.append(uc_detail)

    def add_adjustments(self, adjustments):
        self.adjustments = QuoteAdjustments(adjustments)

    def add(self, misc_name, misc_value):
        # Will overwrite an existing attribute
        if self.misc is None:
            self.misc = _ClassMisc(
                named_attributes=PRICE_ADJUSTED_ATTRIBUTES +
                PRICE_STANDARD_ATTRIBUTES)
        self.misc.add(misc_name, misc_value)

    def add_symbol(self, symbol):
        # For those cases in which the symbol itself needs to be
        # part of a quote
        self.symbol = symbol.upper()

    def get(self, name):
        if name in self.standard_attributes:
            return getattr(self, name)
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


class QuoteSeries(Series):
    # A time-ordered list of quote objects

    def __init__(self, quote_series=None, **kwargs):
        super(QuoteSeries, self).__init__()
        if quote_series is None:
            return
        if not isinstance(quote_series, list):
            raise Exception('Parameter "quote_series" must be a list.')
        reverse_datetime_order = kwargs.pop('reverse_datetime_order', False)
        for quote in quote_series:
            if isinstance(quote, Quote) is False:
                raise Exception('All items in quote_series must be '
                                'of the "Quote" class.')
            self.series.append(quote)
        self.sort('datetime', reverse_datetime_order)
