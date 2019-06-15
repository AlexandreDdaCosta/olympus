# Core application defaults and constants

import datetime

from dateutil.relativedelta import relativedelta

from olympus import DOWNLOAD_DIR

USER = 'larry'

# The following four constants as defined by JLL

CONTINUATION = 3 # An integer that defines the minimum point move required to recognize price continuation
REVERSAL = 6 # An integer that defines the minimum point move required to recognize price reversal
KEY_CONTINUATION = 6 # CONTINUATION for paired analysis of two leading stocks from one industry group
KEY_REVERSAL = 12 # REVERSAL for paired analysis

# Constant hinted at by JLL

SHORT_DISTANCE = .50 # Quantifies Livermore's "short distance" when identifying a pivot point failure

# Key settings

END_CHART = datetime.datetime.now()
START_CHART = datetime.datetime.now() - relativedelta(years=2)
OLDEST_PIVOT = 5 # In years
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

# Text constants

# Trends

UPWARD_TREND = 'Upward Trend'
DOWNWARD_TREND = 'Downward Trend'
NATURAL_RALLY = 'Natural Rally'
NATURAL_REACTION = 'Natural Reaction'
SECONDARY_RALLY = 'Secondary Rally'
SECONDARY_REACTION = 'Secondary Reaction'
UPWARD_TRENDS = [UPWARD_TREND, NATURAL_RALLY, SECONDARY_RALLY]
DOWNWARD_TRENDS = [DOWNWARD_TREND, NATURAL_REACTION, SECONDARY_REACTION]

# Evaluating pivots

# Logic for handling pivots within the CONTINUATION range

PIVOT_LOGIC_OUTER = 'Use only last outlying pivot on trend'
PIVOT_LOGIC_RECENT = 'Use only most recent pivot'
PIVOT_LOGIC_DEFAULT = PIVOT_LOGIC_RECENT
PIVOT_LOGIC = [PIVOT_LOGIC_OUTER,PIVOT_LOGIC_RECENT]

# Pivot price logic

PIVOT_PRICE_ORIGINAL = 'Use original pivot price'
PIVOT_PRICE_ADJUSTED = 'Use adjusted pivot price'
PIVOT_PRICE_LOGIC_DEFAULT = PIVOT_PRICE_ORIGINAL
PIVOT_PRICE_LOGIC = [PIVOT_PRICE_ORIGINAL,PIVOT_PRICE_ADJUSTED]
