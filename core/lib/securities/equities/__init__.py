# Symbols

TEST_SYMBOL_ONE = 'ZIM'
TEST_SYMBOL_ONE_QUOTE_EXCHANGE = 'n'
TEST_SYMBOL_ONE_QUOTE_EXCHANGE_NAME = 'NYSE'
TEST_SYMBOL_TWO = 'AAPL'
TEST_SYMBOL_TWO_QUOTE_EXCHANGE = 'q'
TEST_SYMBOL_TWO_QUOTE_EXCHANGE_NAME = 'NASD'
TEST_SYMBOL_FAKE = 'BADSYMBOL'
TEST_SYMBOL_FAKE_TWO = 'FOOBAR'

SYMBOL = TEST_SYMBOL_ONE

# Signals and positioning

BUY = 'Buy'
SELL = 'Sell'

# Quantities (defaults)

TEST_PURCHASE_SIZE = 100 # Shares

# Miscellaneous

QUOTE_DATE_FORMAT = "%Y-%m-%d"
US_EQUITY_MARKET_HALF_DAYS = [
    '2023-07-03', # Day before Independence Day, if on a weekday and not already closed
    '2024-07-03',
    '2025-07-03',
    '2022-11-25', # Day after Thanksgiving Day; fourth Friday in November
    '2023-11-24',
    '2024-11-29',
    '2025-11-28',
    '2024-12-24', # Christmas Eve, when on a weekday and not already closed
    '2025-12-24'
]
US_EQUITY_MARKET_HOLIDAYS = [
    '2023-01-02', # New Year's Day; January 1st or first Monday following
    '2024-01-01',
    '2025-01-01',
    '2022-01-17', # Martin Luther King, Jr. Day; third Monday in January
    '2023-01-16',
    '2024-01-15',
    '2025-01-20',
    '2022-02-21', # Presidents Day; third Monday in February
    '2023-02-20',
    '2024-02-19',
    '2025-02-17',
    '2022-04-15', # Good Friday
    '2023-04-07',
    '2024-03-29',
    '2025-04-18',
    '2022-05-30', # Memorial Day: last Monday in May
    '2023-05-29',
    '2024-05-27',
    '2025-05-26',
    '2022-06-20', # Juneteenth National Independence Day; July 19. If Saturday, June 18; if Sunday, June 20. First was 2021-06-17.
    '2023-06-19',
    '2024-06-19',
    '2025-06-19',
    '2022-07-04', # Independence Day; July 4. If Saturday, July 3; if Sunday, July 5.
    '2023-07-04',
    '2024-07-04',
    '2025-07-04',
    '2022-09-05', # Labor Day; first Monday in September
    '2023-09-04',
    '2024-09-02',
    '2025-09-01',
    '2022-11-24', # Thanksgiving Day; fourth Thursday in November
    '2023-11-23',
    '2024-11-28',
    '2025-11-27',
    '2021-12-24', # Christmas Day; December 25. If Saturday, December 24; if Sunday, December 26
    '2022-12-26',
    '2023-12-25',
    '2024-12-25',
    '2025-12-25'
]

class TradingDates(object):
    '''
    Information about trading days and hours for US equity markets
    '''

    def __init__(self):
        pass

    def holidays(self,start_date,end_date=None):
        # Returns a list of all trading holidays between two dates, inclusive
        # If no end date is given, will use the current date
        pass

    def half_days(self,start_date,end_date=None):
        # Returns a list of all half trading days between two dates, inclusive
        # On these days, the US stock market closes at 1 PM
        # If no end date is given, will use the current date
        pass

    def trade_days(self,start_date,end_date=None):
        # Returns a count of all dates on which the US equity markets are open
        # between two dates, inclusive.
        # If no end date is given, will use the current date
        '''
        d1 = date(2022, 7, 17)
        d2 = date(2022, 9, 3)
        days = numpy.busday_count( d1, d2 )
        print(days)
        '''
        return 0

