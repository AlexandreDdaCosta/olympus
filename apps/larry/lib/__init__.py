# Core application defaults and constants

import datetime

from dateutil.relativedelta import relativedelta

from olympus import DOWNLOAD_DIR

SYMBOL = 'ba'
USER = 'larry'

CONTINUATION = 3 # An integer that defines the minimum point move required to recognize price continuation
REVERSAL = 6 # An integer that defines the minimum point move required to recognize price reversal
KEY_CONTINUATION = 6 # CONTINUATION for paired analysis of two leading stocks from one industry group
KEY_REVERSAL = 12 # REVERSAL for paired analysis
KEY_THRESHOLD = 250 # Price level at which the analysis uses key price in place of CONTINUATION and REVERSAL

END_CHART = datetime.datetime.now()
START_CHART = datetime.datetime.now() - relativedelta(years=5)
