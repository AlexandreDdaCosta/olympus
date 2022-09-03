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

'''
NASDAQ and NYSE Partial Holidays
(1:00 p.m. Eastern Close)	2022	2023	2024	2025
Day before Independence Day		July 3rd	July 3rd	July 3rd
The Day Following Thanksgiving	November 25th	November 24th	November 29th	November 28th
Christmas Eve
'''
US_EQUITY_MARKET_HALF_DAYS = 
[
]
US_EQUITY_MARKET_HOLIDAYS = 
[
    '2023-01-02', # New Year's Day; Jauary 1st or first Monday following
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
    '2022-06-20', # Juneteenth National Independence Day; July 19. If Saturday, June 18; if Sunday, June 20
    '2023-06-19',
    '2024-06-19',
    '2025-06-19',
    '2022-07-04', # Independence Day; July 4. If Saturday, July 3; if Sunday, July 5
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
