import inspect, os, sys

from argparse import ArgumentParser

DEBUG_LEVELS = (1, 2, 3)
DEFAULT_DEBUG_LEVEL = 1
DEFAULT_VERBOSE = 0

class DebuggerArgs():

    def add_arguments(self):
        parser = ArgumentParser(sys.argv)
        parser.add_argument("-D","--debug",action='store_true',help="Executes built-in pauses with data dumps suitable for deep debugging")
        parser.add_argument("-L","--debug_level",choices=DEBUG_LEVELS,default=DEFAULT_DEBUG_LEVEL,help="Get more debugging output by increasing this setting; levels " + str(DEBUG_LEVELS) + " available; default is '" + str(DEFAULT_DEBUG_LEVEL)  + "'",type=int)
        parser.add_argument("-V","--verbose",action="store_true",help="Chatty output")
        return parser

class Debugger():

    def __init__(self,debug_args=None):
        if debug_args is not None:
            self.args = debug_args
        else:
            debugger_arguments = DebuggerArgs()
            parser = debugger_arguments.add_arguments()
            self.args, unknown = parser.parse_known_args()

    def debug_args(self):
        return self.args

    def debug(self,debug_level=DEFAULT_DEBUG_LEVEL,message='Debug message left blank.',data=None,**kwargs):
        if not self.args.debug:
            return
        if debug_level <= self.args.debug_level:
            print('-----\nDEBUG\n-----\n')
        self.print(message,frame=2)
        if debug_level <= self.args.debug_level:
            if data is not None:
                if type(data) == dict:
                    for item in data:
                        print(item + ': ' + str(data[item]))
                elif type(data) == tuple or type(data) == list:
                    for item in data:
                        print(item)
                else:
                    print(data)
            os.system("/bin/bash -c 'read -s -n 1 -p \"...\"'")
            print()

    def print(self,message='Message left blank.',frame=1):
        if not self.args.verbose and not self.args.debug:
            return
        caller_frame = sys._getframe(frame)
        caller_frameinfo = inspect.getframeinfo(caller_frame)
        sourcefile = inspect.getsourcefile(caller_frame)
        if self.args.debug:
            print("{message} [{sourcefile}, {lineno}]".format(message=message, sourcefile=sourcefile, lineno=caller_frameinfo.lineno))
        else:
            print("{message}".format(message=message))
