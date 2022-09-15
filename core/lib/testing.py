import argparse, inspect, os, pwd, random, re, string, sys, unittest

DEFAULT_STRING_LENGTH = 60
GREP_TEXT = 'Search string located in file.'
NO_GREP_TEXT = 'Search string not found in file.'
NOT_FLOAT_TEXT = 'Value is not a float.'
NOT_NONE_TEXT = 'Value does not equal None.'
MATCH_TEXT = 'Match for regular expression.'
SEARCH_TEXT = 'String located during regular expression search'

TEST_ENVIRONMENT = 'test'
TEST_PREFIX = 'olympustest_'

class Test(unittest.TestCase):

    # Assertions
    
    def assertGrepFile(self,filename,text,description=GREP_TEXT):
        file = open(filename,"r")
        where = file.tell()
        while True:    
            line = file.readline()
            if not line:
                break
            if re.search(text,line):
                file.close()
                return where
            where = file.tell()
        file.close()
        raise AssertionError(description)
    
    def assertInError(self,result):
        if result.in_error():
            raise AssertionError(result.description())
            return True
        return False

    def assertIsFloat(self,value,description=NOT_FLOAT_TEXT):
        try:
            float(value)
            return
        except ValueError:
            raise AssertionError(description)

    def assertIsNone(self,value,description=NOT_NONE_TEXT):
        if value is None:
            return
        raise AssertionError(description)
    
    def assertKeyInDict(self,key,dictionary):
        if key not in dictionary:
            raise AssertionError('Key ' + str(key) + ' not in dict.')

    def assertMatchesRegex(self,string,regex,description=MATCH_TEXT):
        if not regex.match(string):
            raise AssertionError(description)
    
    def assertNotGrepFile(self,filename,text,description=NO_GREP_TEXT):
        file = open(filename,"r")
        where = file.tell()
        while True:    
            line = file.readline()
            if not line:
                break
            if re.search(text,line):
                file.close()
                raise AssertionError(description)
        file.close()
    
    def assertSearchRegex(self,string,regex,description=SEARCH_TEXT):
        if not regex.search(string):
            raise AssertionError(description)
    
    # Utilities

    def file(self):
        caller = inspect.stack()[1]
        return caller[1]

    def function(self):
        caller = inspect.stack()[1]
        return caller[3]

    def line(self):
        caller = inspect.stack()[1]
        return caller[2]

    def random_string(self,length=DEFAULT_STRING_LENGTH):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(length))
    
    def validRunUser(self,username):
        username = str(username)
        uid = os.getuid()
        run_username = pwd.getpwuid(uid)[0]
        if username != run_username:
            raise Exception('Run user ' + run_username + ' does not match required run user ' + username)
        return username
