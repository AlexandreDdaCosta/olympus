# Core constants and classes

import jsonschema, os, re, shutil, stat

from datetime import datetime as dt, timezone
from dateutil import tz
from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError
from os.path import isfile

USER = 'olympus'

ARGON2_CONFIG = { "memory_cost": 64*1024, "parallelism": 1, "salt_bytes": 16, "time_cost": 3 }
CLIENT_CERT='/etc/ssl/localcerts/client-key-crt.pem'
RESTAPI_RUN_USERNAME = 'node'

# Dates
# Formats based on ISO 8601
DATE_STRING_FORMAT = "%Y-%m-%d"
DATETIME_STRING_MILLISECONDS_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# Add-on jsonschema type
def is_datetime(checker,instance):
    # Only timezone-aware datetime allowed
    if isinstance(instance,dt) and instance.tzinfo is not None:
        return True
    return False
VALIDATOR = jsonschema.validators.extend(Draft7Validator,type_checker=Draft7Validator.TYPE_CHECKER.redefine('datetime', is_datetime))

# Services
MONGODB_SERVICE = 'mongodb'
REDIS_SERVICE = 'redis'
RESTAPI_SERVICE = 'restapi'
PASSWORD_ENABLED_SERVICES = [ MONGODB_SERVICE, REDIS_SERVICE, RESTAPI_SERVICE ]

class Dates():

    def utc_date_to_timezone_date(self,utc_date,date_timezone=None):
        # MongoDB assumes all stored dates are UTC, and pymongo also returns dates as UTC.
        # This explains the need for this function
        tz_date = utc_date.replace(tzinfo=timezone.utc)
        if date_timezone is not None:
            # Parameter "timezone" should be the recognized English-language time zone identifier; e.g., "America/New_York"
            date_timezone = tz.gettz(date_timezone)
            return tz_date.astimezone(date_timezone)
        else:
            # By default return using local time zone
            return tz_date.astimezone()

class FileFinder():
    # Retrieves location of system files

    def config_file(self,base_location,config_name):
        return base_location + config_name + '.config'

    def schema_file(self,base_location,schema_name):
        return base_location + schema_name + '.json'

class Return():
    # Stored returned data in object form

    def __init__(self,schema,data):
        if not isinstance(schema,dict):
            raise Exception('Parameter "schema" must be of type dict.')
        if not isinstance(data,dict):
            raise Exception('Parameter "data" must be of type dict.')
        self.Attributes = []
        self.String = String()
        validation_error = None
        try:
            VALIDATOR(schema=schema).validate(data)
        except ValidationError as e:
            validation_error = 'Return data validation error occurred: ' + e.args[0]
        except:
            raise
        if validation_error is not None:
            raise Exception(validation_error)
        for name in data:
            original_name = name
            if schema['properties'][original_name]['type'] == 'null' or data[original_name] == '':
                data[original_name] = None
            if 'convert_name' in schema['properties'][name]:
                # Pascal case name alternative
                name = schema['properties'][name]['convert_name']
            if 'convert_type' in schema['properties'][original_name]:
                # New python data type
                data[original_name] = self._convert_type(data[original_name],schema['properties'][original_name]['convert_type'])
            underscore_name = self.String.pascal_case_to_underscore(name)
            setattr(self,underscore_name,data[original_name])
            self.Attributes.append(underscore_name)

    def add(self,name,value):
        # Add the odd attribute
        name = str(name)
        underscore_name = self.String.pascal_case_to_underscore(name)
        if underscore_name in self.Attributes:
            raise Exception('Attribute ' + str(name) + ' has already been added.')
        setattr(self,underscore_name,value)
        self.Attributes.append(underscore_name)

    def get(self,name):
        if name in self.Attributes:
            return getattr(self,name)
        else:
            underscore_name = self.String.pascal_case_to_underscore(name)
            if underscore_name in self.Attributes:
                return getattr(self,underscore_name)
        return None

    def list(self):
        return sorted(self.Attributes)
    
    def _convert_type(self,data,new_type):
        if data is None:
            return None
        if new_type == 'date_object':
            # This assumes the data is a date string of form DATE_STRING_FORMAT
            return dt.strptime(data, DATE_STRING_FORMAT)
        elif new_type == 'datetime_milliseconds_object':
            # This assumes the data is a date string of form DATETIME_STRING_MILLISECONDS_FORMAT
            return dt.strptime(data, DATETIME_STRING_MILLISECONDS_FORMAT)
        elif new_type == 'integer':
            return int(data)
        elif new_type == 'string':
            return str(data)
        else:
            raise Exception('Unrecognized new data type ' + str(new_type))

class Series():
    # A list of data with object-handling abilities (the default). Preserves order in which items are added unless resorted.

    def __init__(self,**kwargs):
        self.index = 0
        self.series = None
        self.items_type = kwargs.get('items_type',object)

    def add(self,new_item):
        # Add item to series
        if not isinstance(new_item, self.items_type):
            raise Exception('Series object only accepts items of type ' + str(self.items_type) + 'for addition to the series.')
        if self.series is None:
            self.series = []
        self.series.append(new_item)

    def count(self):
        if self.series is None:
            return 0
        return len(self.series)

    def first(self):
        # First item in series
        if self.series is None:
            return None
        return self.series[0]

    def get_by_attribute(self,attribute,value):
        # Returns items in an object series for which an attribute matches a specific value
        if self.series is None:
            return None
        if self.items_type != object:
            raise Exception('This method may only be called for a series of objects.')
        results = None
        for each_object in self.series:
            if hasattr(each_object,attribute) and getattr(each_object,attribute) == value:
                if results is None:
                    results = []
                results.append(each_object)
        if results is None:
            return None
        if len(results) == 1:
            return results[0]
        return results

    def get_by_index(self,index):
        # Get item in series according to fixed order
        if self.series is None:
            return None
        return self.series[index]

    def have_items(self):
        if self.series is None:
            return False
        return True

    def items(self):
        return self.series

    def last(self):
        # Last item in series
        if self.series is None:
            return None
        return self.series[-1]

    def next(self,**kwargs):
        # Used to iterate through the series
        if not self.series:
            return None
        reset = kwargs.pop('reset',False)
        if reset is True:
            self.index = 0
        try:
            item = self.series[self.index]
        except IndexError:
            return None
        self.index = self.index + 1
        return item

    def sort(self,attribute,**kwargs):
        # Sort an object series by an attribute
        print('ALEX INITSORT')
        if self.items_type != object:
            raise Exception('This method may only be called for a series of objects.')
        if self.series is not None:
            reverse = kwargs.get('reverse',False)
            self.series = sorted(self.series, key=lambda s: getattr(s,attribute), reverse=reverse)

class String():
    # Some useful string methods

    def pascal_case_to_underscore(self,string):
        return re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', r'_\1', string).lower().strip('_')

class User():
    # Core user identity and management

    def __init__(self,username=USER):
        self.username=username

    def get_service_password(self,service):
        password_file = self.password_file_name(service)
        if isfile(password_file):
            shutil.chown(password_file,self.username,self.username)
            os.chmod(password_file,stat.S_IREAD | stat.S_IWRITE)
            with open(password_file,'r') as f:
                password = f.readline().rstrip()
            f.close()
            if password == '':
                raise Exception('Password file ' + password_file + ' for user '+self.username+' exists and is readable but is empty.')
            return password
        else:
            # We assume the user is not secured. Calling this procedure with a unprivileged user may lead to exceptions.
            return None

    def password_file_name(self,service):
        if service is None:
            raise Exception('Password protected service must be specified to retrieve password file name.')
        elif service not in PASSWORD_ENABLED_SERVICES:
            raise Exception('Specified service ' + str(service) + ' not among recognized password protected types.')
        return self.etc_directory() + service + '_password'

    def password_file_old_name(self,service):
        return self.password_file_name(service) + '.old'

    def rotate_service_password_file(self,service,password):
        password_file = self.password_file_name(service)
        password_file_old = self.password_file_old_name(service)
        existing_password = None
        old_password = None
        password_file_existed = False
        if isfile(password_file):
            password_file_existed = True
            shutil.chown(password_file,self.username,self.username)
            os.chmod(password_file,stat.S_IREAD | stat.S_IWRITE)
            with open(password_file,'r') as f:
                existing_password = f.readline().rstrip()
            f.close()
        if isfile(password_file_old):
            shutil.chown(password_file_old,self.username,self.username)
            os.chmod(password_file_old,stat.S_IREAD | stat.S_IWRITE)
            with open(password_file_old,'r') as f:
                old_password = f.readline().rstrip()
            f.close()
        if existing_password is not None:
            with open(password_file_old,'w') as f:
                f.write(existing_password)
                f.truncate()
                f.close()
            shutil.chown(password_file_old,self.username,self.username)
            os.chmod(password_file_old,stat.S_IREAD | stat.S_IWRITE)
        with open(password_file,'w') as f:
            f.write(password)
            f.truncate()
            f.close()
        if not password_file_existed:
            shutil.chown(password_file,self.username,self.username)
            os.chmod(password_file,stat.S_IREAD | stat.S_IWRITE)

    def download_directory(self):
        return self.home_directory() + 'Downloads/'

    def etc_directory(self):
        return self.home_directory() + 'etc/'

    def home_directory(self):
        return '/home/' + self.username +'/'

    def mongo_database(self):
        return 'user:' + self.username

    def lockfile_directory(self):
        return self.working_directory()

    def working_directory(self):
        return '/var/run/' + USER + '/apps/' + self.username + '/'
