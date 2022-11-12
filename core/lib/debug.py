import inspect, json, os, sys

from argparse import ArgumentParser

DEBUG_LEVELS = (1, 2, 3)
DEFAULT_DEBUG_LEVEL = 1
DEFAULT_VERBOSE = 0

class DebuggerArgs():

    def add_arguments(self):
        parser = ArgumentParser(sys.argv)
        parser.add_argument("-D","--debug",action='store_true',help="Executes built-in pauses with data dumps suitable for deep debugging")
        parser.add_argument("-L","--debug_level",choices=DEBUG_LEVELS,default=DEFAULT_DEBUG_LEVEL,help="Get more debugging output by increasing this setting; levels " + str(DEBUG_LEVELS) + " available; default is '" + str(DEFAULT_DEBUG_LEVEL)  + "'",type=int)
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
        caller_frame = sys._getframe(1)
        caller_frameinfo = inspect.getframeinfo(caller_frame)
        sourcefile = inspect.getsourcefile(caller_frame)
        if debug_level <= self.args.debug_level:
            if self.args.debug_level == 1:
                print("{message}".format(message=message))
            else:
                print("{message} [{sourcefile}, {lineno}]".format(message=message, sourcefile=sourcefile, lineno=caller_frameinfo.lineno))
            if data is not None and self.args.debug_level >= 2:
                if isinstance(data, object) and hasattr(data, '__dict__'):
                    print(json.dumps(vars(data), default=str, indent=4, sort_keys=True))
                else:
                    print(json.dumps(data, default=str, indent=4, sort_keys=True))
                if debug_level > 1 and debug_level == self.args.debug_level:
                    import subprocess
                    result = subprocess.run(["/bin/bash -c 'read -n 1 -s -p \"<<<<\" input; echo $input'"], stdout=subprocess.PIPE, shell=True)
                    if b'q' in result.stdout:
                        print('\nDebugger halting due to user input; exiting ...')
                        quit()
                    print()
                else:
                    print('.')
