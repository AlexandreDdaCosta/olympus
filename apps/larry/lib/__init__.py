# Core application defaults and constants

import datetime
from dateutil.relativedelta import relativedelta

from olympus import DOWNLOAD_DIR

SYMBOL = 'ba'
USER = 'larry'

# The following four constants as defined by JLL

CONTINUATION = 3 # An integer that defines the minimum point move required to recognize price continuation
REVERSAL = 6 # An integer that defines the minimum point move required to recognize price reversal
SHORT_DISTANCE = .50 # Quantifies Livermore's "short distance" when identifying a pivot point failure
KEY_CONTINUATION = 6 # CONTINUATION for paired analysis of two leading stocks from one industry group
KEY_REVERSAL = 12 # REVERSAL for paired analysis

END_CHART = datetime.datetime.now()
START_CHART = datetime.datetime.now() - relativedelta(years=5)

THRESHOLDS = [
    {
        'Continuation' : 1,
        'Maximum' : 20,
        'Reversal' : 2,
        'Short Distance' : .20
    },
    {
        'Continuation' : 2,
        'Maximum' : 30,
        'Reversal' : 4,
        'Short Distance' : .25
    },
    {
        'Continuation' : CONTINUATION,
        'Maximum' : 250,
        'Reversal' : REVERSAL,
        'Short Distance' : .50
    },
    {
        'Continuation' : 6,
        'Maximum' : 500,
        'Reversal' : 12,
        'Short Distance' : 1
    },
    {
        'Continuation' : 12,
        'Maximum' : 1000,
        'Reversal' : 24,
        'Short Distance' : 3
    },
    {
        'Continuation' : 50,
        'Maximum' : 10000,
        'Reversal' : 100,
        'Short Distance' : 10
    },
    {
        'Continuation' : 500,
        'Maximum' : 100000,
        'Reversal' : 1000,
        'Short Distance' : 100
    },
    {
        'Continuation' : 5000,
        'Reversal' : 10000,
        'Short Distance' : 1000
    }
]

# Trade backtesting defaults

COMMISSION = 8 # Dollars per trade
STOP_LOSS = .94 # Six percent stop loss on buy/short sell
TRADE_SIZE = 100 # Shares
