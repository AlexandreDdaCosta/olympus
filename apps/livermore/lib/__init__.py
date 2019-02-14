# Core application constants

from olympus import DOWNLOAD_DIR

USER = 'livermore'

CONTINUE = 3 # An integer that defines the minimum point move required to recognize price continuation
REVERSAL = 6 # An integer that defines the minimum point move required to recognize price reversal

# These functions continuation and reversal levels for multiple equities
def KEY_CONTINUE(securities=2,continuation=CONTINUE):
    return securities * continuation
def KEY_REVERSAL(securities=2,reversal=REVERSAL):
    return securities * reversal
