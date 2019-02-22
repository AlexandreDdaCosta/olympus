# Core application defaults and constants

import datetime
from dateutil.relativedelta import relativedelta

from olympus import DOWNLOAD_DIR

SYMBOL = 'ba'
USER = 'larry'

# The following four constants as defined by JLL

CONTINUATION = 3 # An integer that defines the minimum point move required to recognize price continuation
REVERSAL = 6 # An integer that defines the minimum point move required to recognize price reversal
KEY_CONTINUATION = 6 # CONTINUATION for paired analysis of two leading stocks from one industry group
KEY_REVERSAL = 12 # REVERSAL for paired analysis

END_CHART = datetime.datetime.now()
START_CHART = datetime.datetime.now() - relativedelta(years=5)

THRESHOLDS = [
    {
        'Continuation' : 1,
        'Maximum' : 20,
        'Reversal' : 2
    },
    {
        'Continuation' : 2,
        'Maximum' : 30,
        'Reversal' : 4
    },
    {
        'Continuation' : CONTINUATION,
        'Maximum' : 250,
        'Reversal' : REVERSAL
    },
    {
        'Continuation' : 6,
        'Maximum' : 500,
        'Reversal' : 12
    },
    {
        'Continuation' : 12,
        'Maximum' : 1000,
        'Reversal' : 24
    },
    {
        'Continuation' : 50,
        'Maximum' : 10000,
        'Reversal' : 100
    },
    {
        'Continuation' : 500,
        'Maximum' : 100000,
        'Reversal' : 1000
    },
    {
        'Continuation' : 5000,
        'Reversal' : 10000
    }
]

# Trade backtesting defaults

COMMISSION = 8 # Dollars per trade
PURCHASE_SIZE = 100 # Shares
