# Core application constants

from olympus import DOWNLOAD_DIR

SYMBOL = 'ba'
USER = 'livermore'

CONTINUATION = 3 # An integer that defines the minimum point move required to recognize price continuation
REVERSAL = 6 # An integer that defines the minimum point move required to recognize price reversal

# These functions return eontinuation and reversal levels for multiple equities
def KEY_CONTINUATION(securities=2,continuation=CONTINUATION):
    return securities * continuation
def KEY_REVERSAL(securities=2,reversal=REVERSAL):
    return securities * reversal
