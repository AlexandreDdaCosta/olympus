import os

# Exchanges

NASDAQ = 'nasdaq'
NYSE = 'nyse'

# Symbols

TEST_SYMBOL_DIV = 'ZIM'  # Dividends but no splits
TEST_SYMBOL_DIV_EXCHANGE = NYSE
TEST_SYMBOL_DIV_QUOTE_EXCHANGE = 'n'
TEST_SYMBOL_DIV_QUOTE_EXCHANGE_NAME = 'NYSE'
TEST_SYMBOL_DIVSPLIT = 'AAPL'  # Dividends and splits
TEST_SYMBOL_DIVSPLIT_EXCHANGE = NASDAQ
TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE = 'q'
TEST_SYMBOL_DIVSPLIT_QUOTE_EXCHANGE_NAME = 'NASD'
TEST_SYMBOL_ETF = 'SPY'
TEST_SYMBOL_INDEX = 'SPX'
TEST_SYMBOL_SPLIT = 'AMZN'  # Splits but no dividends
TEST_SYMBOL_SPLIT_EXCHANGE = NASDAQ
TEST_SYMBOL_SPLIT_QUOTE_EXCHANGE = 'q'
TEST_SYMBOL_SPLIT_QUOTE_EXCHANGE_NAME = 'NASD'
TEST_SYMBOL_NODIVSPLIT = 'TWLO'  # No splits or dividends
TEST_SYMBOL_NODIVSPLIT_EXCHANGE = NYSE
TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE = 'n'
TEST_SYMBOL_NODIVSPLIT_QUOTE_EXCHANGE_NAME = 'NYSE'
TEST_SYMBOL_FAKE = 'BADSYMBOL'
TEST_SYMBOL_FAKE_TWO = 'FOOBAR'
TEST_SYMBOLS = [
        TEST_SYMBOL_DIVSPLIT,
        TEST_SYMBOL_DIV,
        TEST_SYMBOL_SPLIT,
        TEST_SYMBOL_NODIVSPLIT]

SYMBOL = TEST_SYMBOL_DIVSPLIT

# Classes of equity symbols

INDEX_CLASS = 'Index'
SECURITY_CLASS_ETF = 'ETF'
SECURITY_CLASS_STOCK = 'Stock'

# Quantities (defaults)

STOP_LOSS = .98  # Two percent stop loss on buy/short
TEST_PURCHASE_SIZE = 100  # Shares

# Miscellaneous

CONFIG_FILE_DIRECTORY = os.path.dirname(
        os.path.realpath(__file__)) + '/config/'
SCHEMA_FILE_DIRECTORY = os.path.dirname(
        os.path.realpath(__file__)) + '/schema/'

# These settings are temporary
REGULAR_MARKET_OPEN_TIME = '09:30:00'
REGULAR_MARKET_CLOSE_TIME = '16:00:00'
SHORTENED_MARKET_CLOSE_TIME = '13:00:00'
