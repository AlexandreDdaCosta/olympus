"""
Core testing module, inheriting unittest while adding more methods.
"""

import inspect
import json
import jsonschema
import os
import pwd
import random
import re
import string
import sys
import time
import unittest

from argparse import ArgumentError, ArgumentParser
from filelock import Timeout, FileLock
from os.path import isfile, join
from types import SimpleNamespace

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

parser = ArgumentParser(sys.argv,  # pyright: ignore
                        conflict_handler='resolve')
parser.add_argument('-t', '--test',
                    action='store',
                    default='all',
                    help='Specify the name of a single test to run.')
parser.add_argument('-u', '--username',
                    action='store',
                    default=pwd.getpwuid(os.getuid())[0],
                    help='Specify a user name under which test should run.')
parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Chatty output.')


class Test(unittest.TestCase):

    arguments = None
    username = None
    parser_args = []

    @classmethod
    def setUpClass(cls, **kwargs):
        if len(Test.parser_args) > 0:
            for parser_arg in Test.parser_args:
                kwargs = {}
                if len(parser_arg) > 2:
                    if 'action' in parser_arg[2]:
                        kwargs['action'] = parser_arg[2]['action']
                    if 'choices' in parser_arg[2]:
                        kwargs['choices'] = parser_arg[2]['choices']
                    if 'default' in parser_arg[2]:
                        kwargs['default'] = parser_arg[2]['default']
                    if 'help' in parser_arg[2]:
                        kwargs['help'] = parser_arg[2]['help']
                parser.add_argument(parser_arg[0], parser_arg[1], **kwargs)
        Test.arguments, extra = parser.parse_known_args()  # pyright: ignore
        run_username = pwd.getpwuid(os.getuid())[0]
        if str(Test.arguments.username) != run_username:
            raise Exception(f'Run user {run_username} does not match required '
                            'run user ' + str(Test.arguments.username))
        Test.username = Test.arguments.username

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
            args = parser.parse_args()
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
        if Test.arguments.verbose is True:   # pyright: ignore
            print(message)

    def print_test(self, test):
        if Test.arguments.verbose is True:   # pyright: ignore
            print(f'Test: {test}.')

    def random_string(self, length=DEFAULT_STRING_LENGTH):
        return ''.join(
            random.choice(string.ascii_uppercase + string.digits)
            for x in range(length))   # pyright: ignore

    def skip_test(self):
        test_case = re.sub('^test_',
                           '',
                           inspect.getframeinfo(sys._getframe(1)).function)
        if (Test.arguments.test != 'all' and  # pyright: ignore
                Test.arguments.test != test_case):  # pyright: ignore
            self.print('\nSkip test: ' + test_case + '.')
            return True
        return False


class TestConfig(object):

    def __init__(self, test_path, **kwargs):  # noqa: C901
        """
        Reads suite-style configuration files and verifies them against
        any existing jsonschema.

        The overall testing structure envisioned here is as follows:

        application/tests: Location of testing files.
        application/tests/config.json: Main configuration file.
        application/tests/data/*.json: All data files needed for tests.
        application/tests/schema/*.json: All jsonschema files to match
        data files.
        """
        self.test_path = test_path
        config_file_name = kwargs.pop('config_file_name', 'config.json')
        conf_file = self.test_path + os.path.sep + config_file_name
        if os.path.exists(conf_file):
            with open(conf_file) as f:
                self.config = json.load(f, object_hook=self._dict_to_namespace)
        data_dir = (self.test_path +
                    os.path.sep +
                    kwargs.pop('data_dir', 'data'))
        if os.path.exists(data_dir):
            data_files = [f for f in os.listdir(data_dir)
                          if isfile(join(data_dir, f))]
            for data_file in data_files:
                if re.match(r".*\.json$", data_file):
                    attribute = re.sub(r"(.*)\.json", r'\1', data_file)
                    conf_file = data_dir + os.path.sep + data_file
                    with open(conf_file) as f:
                        setattr(self, attribute, json.loads(f.read()))
        schema_dir = (self.test_path +
                      os.path.sep +
                      kwargs.pop('schema_dir', 'schema'))
        validated = True
        if os.path.exists(schema_dir):
            schema_files = [f for f in os.listdir(data_dir)
                            if isfile(join(data_dir, f))]
            for schema_file in schema_files:
                if re.match(r".*\.json$", schema_file):
                    data_file = data_dir + os.path.sep + schema_file
                    json_schema_file = schema_dir + os.path.sep + schema_file
                    validate_id_field = False
                    if os.path.exists(data_file):
                        attribute = re.sub(r"(.*)\.json", r'\1', schema_file)
                        with open(json_schema_file) as f:
                            schema = json.loads(f.read())
                            if 'jid' in schema['items']['properties']:
                                validate_id_field = True
                        try:
                            jsonschema.validate(
                                instance=getattr(self, attribute),
                                schema=schema)
                        except jsonschema.ValidationError as e:
                            print(e)
                            validated = False
                        if validate_id_field:
                            data = getattr(self, attribute)
                            if len(data) != len(set({d['jid'] for d in data})):
                                print(f"Duplicate JID detected in {data_file}")
                                validated = False
        if validated is False:
            raise Exception('Data files failed json schema validation.')

    def lock(self, path):
        sleep = 5
        timeout = 1
        retry = 5
        lockfile = (path +
                    re.escape(os.path.sep) +
                    'misc' +
                    re.escape(os.path.sep) +
                    'tests.LOCK')
        locked = False
        retries = 0
        self.lock = FileLock(lockfile, timeout=timeout)  # pyright: ignore
        while locked is False:
            try:
                self.lock.acquire()
                break
            except Timeout:
                retries += 1
                if retries >= retry:
                    raise
                print(f"Sleeping for {sleep} seconds waiting for lock.")
                time.sleep(sleep)

    def _dict_to_namespace(self, d):
        return SimpleNamespace(**d)
