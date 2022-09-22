# Core constants and classes

import os, re, shutil, stat

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from os.path import isfile

USER = 'olympus'

ARGON2_CONFIG = { "memory_cost": 64*1024, "parallelism": 1, "salt_bytes": 16, "time_cost": 3 }
CLIENT_CERT='/etc/ssl/localcerts/client-key-crt.pem'
MONGODB_SERVICE = 'mongodb'
REDIS_SERVICE = 'redis'
RESTAPI_RUN_USERNAME = 'node'
RESTAPI_SERVICE = 'restapi'

PASSWORD_ENABLED_SERVICES = [ MONGODB_SERVICE, REDIS_SERVICE, RESTAPI_SERVICE ]

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
            validate(instance=data,schema=schema)
        except ValidationError as e:
            validation_error = 'Return data validation error occurred: ' + e.args[0]
        except:
            raise
        if validation_error is not None:
            raise Exception(validation_error)
        for name in data:
            original_name = name
            if 'convert_name' in schema['properties'][name]:
                # Pascal case name alternative
                name = schema['properties'][name]['convert_name']
            if 'convert_type' in schema['properties'][original_name]:
                # New python data type
                data[original_name] = self._convert_type(data[original_name],schema['properties'][original_name]['convert_type'])
            if schema['properties'][original_name]['type'] == 'null' or data[original_name] == '':
                data[original_name] = None
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
        if new_type == 'string':
            return str(data)
        elif new_type == 'integer':
            return int(data)
        else:
            raise Exception('Unrecognized new data type ' + str(new_type))

class Series():
    # A list of objects. Preserves order in which objects are added unless resorted.

    def __init__(self):
        self.index = 0
        self.series = None

    def add(self,new_object):
        # Add object to series
        if not isinstance(new_object, object):
            raise Exception('Series object only accepts other objects for addition to the series.')
        if self.series is None:
            self.series = []
        self.series.append(new_object)

    def first(self):
        # First object in series
        if self.series is None:
            return None
        return self.series[0]

    def get_by_attribute(self,attribute,value):
        # Returns all objects in a series for which the attribute matches a specific value
        if self.series is None:
            return None
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
        # Get object in series according to fixed order
        if self.series is None:
            return None
        return self.series[index]

    def have_objects(self):
        if self.series is None:
            return False
        return True

    def last(self):
        # Last object in series
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

    def objects(self):
        return self.series

    def sort(self,attribute,reverse=False):
        # Sort the series by an object attribute
        if self.series is not None:
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
