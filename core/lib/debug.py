import inspect, os, sys

from argparse import ArgumentError, ArgumentParser

DEBUG_LEVELS = (1, 2, 3)
DEFAULT_DEBUG_LEVEL = 1
DEFAULT_VERBOSE = 0

parser = ArgumentParser(sys.argv)
parser.add_argument("-D","--debug",action='store_true',help="Executes built-in pauses with data dumps suitable for deep debugging")
parser.add_argument("-L","--debug_level",default=DEFAULT_DEBUG_LEVEL,help="Get more debugging output by increasing this setting; levels " + str(DEBUG_LEVELS) + " available; default is '" + str(DEFAULT_DEBUG_LEVEL)  + "'")
parser.add_argument("-V","--verbose",action="store_true",help="Chatty output")

class DebuggerArgs():

    def add_arguments(self):
        parser = ArgumentParser(sys.argv)
        parser.add_argument("-D","--debug",action='store_true',help="Executes built-in pauses with data dumps suitable for deep debugging")
        parser.add_argument("-L","--debug_level",default=DEFAULT_DEBUG_LEVEL,help="Get more debugging output by increasing this setting; levels " + str(DEBUG_LEVELS) + " available; default is '" + str(DEFAULT_DEBUG_LEVEL)  + "'")
        parser.add_argument("-V","--verbose",action="store_true",help="Chatty output")
        return parser

class Debugger():

    def __init__(self,**kwargs):
        debugger_arguments = DebuggerArgs()
        parser = debugger_arguments.add_arguments()
        self.args, unknown = parser.parse_known_args()
        self.last_source_file = None

    def debug(self,message='Debug message left blank.',debug_level=DEFAULT_DEBUG_LEVEL,data=None,**kwargs):
        if not self.args.debug:
            return
        self.print(message)
        if self.args.debug_level <= debug_level:
            if data is not None:
                for item in data:
                    print(item)
            os.system("/bin/bash -c 'read -s -n 1 -p \"....\"'")
            print()

    def print(self,message='Message left blank.'):
        if not self.args.verbose and not self.args.debug:
            return
        caller_frame = sys._getframe(1)
        caller_frameinfo = inspect.getframeinfo(caller_frame)
        sourcefile = inspect.getsourcefile(caller_frame)
        if sourcefile == self.last_source_file:
            sourcefile = '... ' + os.path.basename(sourcefile)
        else:
            self.last_source_file = sourcefile
        if self.args.debug:
            print("{message} [{sourcefile}, {lineno}]".format(message=message, sourcefile=sourcefile, lineno=caller_frameinfo.lineno))
        else:
            print("{message}".format(message=message))
