from optparse import OptionParser

import inspect, random, re, string, sys, unittest

DEFAULT_STRING_LENGTH = 60
GREP_TEXT = 'Search string located in file.'
NO_GREP_TEXT = 'Search string not found in file.'
NOT_NONE_TEXT = 'Search string not found in file.'
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

	def assertIsNone(self,value,description=NOT_NONE_TEXT):
		if value is None:
			return
		raise AssertionError(description)
	
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

	def add_option(self,*args,**kwargs):
		if not hasattr(self,'parser'):
			self.parser = OptionParser()
		self.parser.add_option(*args,**kwargs)

	def arguments(self):
		if not hasattr(self,'parser'):
			self.parser = OptionParser()
		if not self._is_opt_defined(self.parser,'env'):
			self.parser.add_option("-e","--env",default=TEST_ENVIRONMENT,help="Environment under which test is running")
		self.args, command_string = self.parser.parse_args()

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

	def _is_opt_defined(self,parser,dest):
		for option in parser._get_all_options():
			if option.dest == dest:
				return True
		return False  	
