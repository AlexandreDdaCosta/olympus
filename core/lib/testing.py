import inspect
import os
import pwd
import random
import re
import string
import sys
import unittest

from argparse import ArgumentError, ArgumentParser

DEFAULT_STRING_LENGTH = 60
GREP_TEXT = 'Search string located in file.'
NO_GREP_TEXT = 'Search string not found in file.'
NONE_TEXT = 'Value equals None.'
NOT_FLOAT_TEXT = 'Value is not a float.'
NOT_NONE_TEXT = 'Value does not equal None.'
MATCH_TEXT = 'Match for regular expression.'
SEARCH_TEXT = 'String located during regular expression search.'
XOR_TEXT = 'One or the other value must be true, but both cannot be.'

TEST_ENVIRONMENT = 'test'
TEST_PREFIX = 'olympustest_'

parser = ArgumentParser(sys.argv, conflict_handler='resolve')
parser.add_argument('-u', '--username',
                    action='store',
                    default=pwd.getpwuid(os.getuid())[0],
                    help='Specify a user name under which test should run.')
parser.add_argument('-t', '--test',
                    action='store',
                    default='all',
                    help='Specify the name of a single test to run.')
parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Chatty output.')


class Test(unittest.TestCase):

    def __init__(self, test_case, **kwargs):
        parser_args = kwargs.pop('parser_args', None)
        super(Test, self).__init__(test_case)
        if parser_args is not None:
            for parser_arg in parser_args:
                action = None
                choices = None
                default = None
                help = None
                if len(parser_arg) > 2:
                    if 'action' in parser_arg[2]:
                        action = parser_arg[2]['action']
                    if 'choices' in parser_arg[2]:
                        choices = parser_arg[2]['choices']
                    if 'default' in parser_arg[2]:
                        default = parser_arg[2]['default']
                    if 'help' in parser_arg[2]:
                        help = parser_arg[2]['help']
                parser.add_argument(
                        parser_arg[0],
                        parser_arg[1],
                        action=action,
                        choices=choices,
                        default=default,
                        help=help
                        )
        self.args = parser.parse_args()
        self.username = self.validRunUser(self.args.username)

    # Assertions

    def assertGrepFile(self, filename, text, description=GREP_TEXT):
        file = open(filename, "r")
        where = file.tell()
        while True:
            line = file.readline()
            if not line:
                break
            if re.search(text, line):
                file.close()
                return where
            where = file.tell()
        file.close()
        raise AssertionError(description)

    def assertInError(self, result):
        if result.in_error():
            raise AssertionError(result.description())
            return True
        return False

    def assertIsFloat(self, value, description=NOT_FLOAT_TEXT):
        try:
            float(value)
            return
        except ValueError:
            raise AssertionError(description)

    def assertIsNone(self, value, description=NOT_NONE_TEXT):
        if value is None:
            return
        raise AssertionError(description)

    def assertIsNotNone(self, value, description=NONE_TEXT):
        if value is not None:
            return
        raise AssertionError(description)

    def assertKeyInDict(self, key, dictionary):
        if key not in dictionary:
            raise AssertionError('Key ' + str(key) + ' not in dict.')

    def assertMatchesRegex(self, string, regex, description=MATCH_TEXT):
        if not regex.match(string):
            raise AssertionError(description)

    def assertNotGrepFile(self, filename, text, description=NO_GREP_TEXT):
        file = open(filename, "r")
        while True:
            line = file.readline()
            if not line:
                break
            if re.search(text, line):
                file.close()
                raise AssertionError(description)
        file.close()

    def assertSearchRegex(self, string, regex, description=SEARCH_TEXT):
        if not regex.search(string):
            raise AssertionError(description)

    def assertXor(self, x, y, description=XOR_TEXT):
        if not bool((x and not y) or (not x and y)):
            raise AssertionError(description)

    # Utilities

    def add_argument(self, *args, **kwargs):
        try:
            parser.add_argument(*args, **kwargs)
            self.args = parser.parse_args()
        except ArgumentError:
            pass
        except Exception:
            raise

    def file(self):
        caller = inspect.stack()[1]
        return caller[1]

    def function(self):
        caller = inspect.stack()[1]
        return caller[3]

    def line(self):
        caller = inspect.stack()[1]
        return caller[2]

    def print(self, message):
        if self.args.verbose is True:
            print(message)

    def print_test(self, test):
        if self.args.verbose is True:
            print(f'Test: {test}.')

    def random_string(self, length=DEFAULT_STRING_LENGTH):
        return ''.join(
                random.choice(string.ascii_uppercase + string.digits)
                for x in range(length))

    def skip_test(self):
        test_case = re.sub('^test_',
                           '',
                           inspect.getframeinfo(sys._getframe(1)).function)
        if self.args.test != 'all' and self.args.test != test_case:
            self.print('\nSkip test: ' + test_case + '.')
            return True
        return False

    def validRunUser(self, username):
        username = str(username)
        uid = os.getuid()
        run_username = pwd.getpwuid(uid)[0]
        if username != run_username:
            raise Exception(f'Run user {run_username} does not match '
                            'required run user {username}')
        return username
