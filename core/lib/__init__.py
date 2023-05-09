# Core constants and classes

import jsonschema
import os
import re
import shutil
import stat

from datetime import datetime as dt, timezone
from dateutil import tz
from jsonschema import Draft7Validator
from jsonschema.exceptions import ValidationError
from os.path import isfile

USER = 'olympus'

ARGON2_CONFIG = {"memory_cost": 64*1024,
                 "parallelism": 1,
                 "salt_bytes": 16,
                 "time_cost": 3}
CLIENT_CERT = '/etc/ssl/localcerts/client-key-crt.pem'
RESTAPI_RUN_USERNAME = 'node'

# Dates
# Formats based on ISO 8601
DATE_STRING_FORMAT = "%Y-%m-%d"
DATETIME_STRING_MILLISECONDS_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# Add-on jsonschema type


def is_datetime(checker, instance):
    # Only timezone-aware datetime allowed
    if isinstance(instance, dt) and instance.tzinfo is not None:
        return True
    return False


TYPE_CHECKER = Draft7Validator.TYPE_CHECKER.redefine('datetime', is_datetime)
VALIDATOR = jsonschema.validators.extend(
        Draft7Validator,
        type_checker=TYPE_CHECKER)

# Services
MONGODB_SERVICE = 'mongodb'
REDIS_SERVICE = 'redis'
RESTAPI_SERVICE = 'restapi'
PASSWORD_ENABLED_SERVICES = [MONGODB_SERVICE, REDIS_SERVICE, RESTAPI_SERVICE]


class Dates():

    def utc_date_to_tz_date(self, utc_date, date_timezone=None):
        # MongoDB assumes all stored dates are UTC, and pymongo also returns
        # dates as UTC. This explains the need for this function
        tz_date = utc_date.replace(tzinfo=timezone.utc)
        if date_timezone is not None:
            # Parameter "timezone" should be the recognized English-language
            # time zone identifier; e.g., "America/New_York"
            date_timezone = tz.gettz(date_timezone)
            return tz_date.astimezone(date_timezone)
        else:
            # By default return using local time zone
            return tz_date.astimezone()


class FileFinder():
    # Retrieves location of system files

    def config_file(self, base_location, config_name):
        return base_location + config_name + '.config'

    def schema_file(self, base_location, schema_name):
        return base_location + schema_name + '.json'


class Return():
    # Stores returned data in object form

    def __init__(self, data, schema, **kwargs):  # noqa: F403
        if not isinstance(schema, dict):
            raise Exception('Parameter "schema" must be of type dict.')
        if not isinstance(data, dict):
            raise Exception('Parameter "data" must be of type dict.')
        no_data_validation = kwargs.get('no_data_validation', False)
        self.Attributes = []
        self.String = String()
        if no_data_validation is False:
            validation_error = None
            try:
                VALIDATOR(schema=schema).validate(data)
            except ValidationError as e:
                error_string = 'Return data validation error occurred: '
                validation_error = error_string + e.args[0]
            except Exception:
                raise
            if validation_error is not None:
                raise Exception(validation_error)
        for name in data:
            original_name = name
            type_name = schema['properties'][original_name]['type']
            if type_name == 'null' or data[original_name] == '':
                data[original_name] = None
            if 'convert_name' in schema['properties'][name]:
                # Pascal case name alternative
                name = schema['properties'][name]['convert_name']
            if 'convert_type' in schema['properties'][original_name]:
                # New python data type
                new_type = schema['properties'][original_name]['convert_type']
                data[original_name] = self._convert_type(data[original_name],
                                                         new_type)
            underscore_name = self.String.pascal_case_to_underscore(name)
            setattr(self, underscore_name, data[original_name])
            self.Attributes.append(underscore_name)
            if 'duplicate_as' in schema['properties'][original_name]:
                old_name = schema['properties'][original_name]['duplicate_as']
                underscored = self.String.pascal_case_to_underscore(old_name)
                if 'duplicate_value' in schema['properties'][original_name]:
                    dv = schema['properties'][original_name]['duplicate_value']
                    data[original_name] = dv
                setattr(self, underscored, data[original_name])
                self.Attributes.append(underscored)

    def __repr__(self):
        return "Return(%s)" % (self.__dict__)

    def add(self, name, value):
        # Add the odd attribute
        name = str(name)
        underscore_name = self.String.pascal_case_to_underscore(name)
        if underscore_name in self.Attributes:
            raise Exception(f'Attribute {name} has already been added.')
        setattr(self, underscore_name, value)
        self.Attributes.append(underscore_name)

    def get(self, name):
        if name in self.Attributes:
            return getattr(self, name)
        else:
            underscore_name = self.String.pascal_case_to_underscore(name)
            if underscore_name in self.Attributes:
                return getattr(self, underscore_name)
        return None

    def list(self):
        return sorted(self.Attributes)

    def _convert_type(self, data, new_type):
        if data is None:
            return None
        if new_type == 'date_object':
            # This assumes the data is a date string of form DATE_STRING_FORMAT
            return dt.strptime(data, DATE_STRING_FORMAT)
        elif new_type == 'datetime_milliseconds_object':
            # This assumes the data is a date string of form
            # DATETIME_STRING_MILLISECONDS_FORMAT
            return dt.strptime(data, DATETIME_STRING_MILLISECONDS_FORMAT)
        elif new_type == 'integer':
            return int(data)
        elif new_type == 'string':
            return str(data)
        else:
            raise Exception('Unrecognized new data type ' + str(new_type))


class Series():
    # A list of data with object-handling abilities (the default).
    # Preserves order in which items are added unless resorted.

    def __init__(self, **kwargs):
        self.index = 0
        self.series = None
        self.items_type = kwargs.get('items_type', object)
        self.reverse_sort = None
        self.sort_attribute = None

    def add(self, new_item):
        # Add item to series
        if not isinstance(new_item, self.items_type):
            raise Exception('Series object only accepts items of type '
                            f'{self.items_type} for addition to the series.')
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

    def get_by_attribute(self, attribute, value):
        # Returns items in an object series for which an attribute
        # matches a specific value
        if self.series is None:
            return None
        if self.items_type != object:
            raise Exception('This method may only be called '
                            'for a series of objects.')
        results = None
        for each_object in self.series:
            if hasattr(each_object, attribute) and \
               getattr(each_object, attribute) == value:
                if results is None:
                    results = []
                results.append(each_object)
        if results is None:
            return None
        if len(results) == 1:
            return results[0]
        return results

    def get_by_index(self, index):
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

    def lookback(self, positions):
        # Retrieves past items in relation to current index
        lookback_index = self.index - int(positions)
        if lookback_index < 0:
            return None
        return self.series[lookback_index]

    def next(self, **kwargs):
        # Used to iterate through the series
        if not self.series:
            return None
        reset = kwargs.pop('reset', False)
        if reset is True:
            self.index = 0
        try:
            item = self.series[self.index]
        except IndexError:
            return None
        self.index = self.index + 1
        return item

    def sort(self, attribute, **kwargs):
        # Sort an object series by an attribute
        if self.items_type != object:
            raise Exception('This method may only be called for '
                            'a series of objects.')
        reverse = kwargs.get('reverse', False)
        # Re-use last sort if possible:
        if self.reverse_sort is not None:
            if self.sort_attribute == attribute and \
               self.reverse_sort == reverse:
                return
        if self.series is not None:
            self.series = sorted(self.series,
                                 key=lambda s: getattr(s, attribute),
                                 reverse=reverse)
            self.reverse_sort = reverse
            self.sort_attribute = attribute


class String():
    # Some useful string methods

    def pascal_case_to_underscore(self, string):
        return re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', r'_\1',
                      string).lower().strip('_')


class User():
    # Core user identity and management

    def __init__(self, username=USER):
        self.username = username

    def get_service_password(self, service):
        password_file = self.password_file_name(service)
        if isfile(password_file):
            shutil.chown(password_file, self.username, self.username)
            os.chmod(password_file, stat.S_IREAD | stat.S_IWRITE)
            with open(password_file, 'r') as f:
                password = f.readline().rstrip()
            f.close()
            if password == '':
                raise Exception(f'Password file {password_file} for user '
                                f'{self.username} exists and is readable '
                                'but is empty.')
            return password
        else:
            # We assume the user is not secured. Calling this procedure with
            # an unprivileged user may lead to exceptions.
            return None

    def password_file_name(self, service):
        if service is None:
            raise Exception('Password protected service must be specified '
                            'to retrieve password file name.')
        elif service not in PASSWORD_ENABLED_SERVICES:
            raise Exception(f'Specified service {service} not among recognized'
                            'password protected types.')
        return self.etc_directory() + service + '_password'

    def password_file_old_name(self, service):
        return self.password_file_name(service) + '.old'

    def rotate_service_password_file(self, service, password):
        password_file = self.password_file_name(service)
        password_file_old = self.password_file_old_name(service)
        existing_password = None
        password_file_existed = False
        if isfile(password_file):
            password_file_existed = True
            shutil.chown(password_file, self.username, self.username)
            os.chmod(password_file, stat.S_IREAD | stat.S_IWRITE)
            with open(password_file, 'r') as f:
                existing_password = f.readline().rstrip()
            f.close()
        if isfile(password_file_old):
            shutil.chown(password_file_old, self.username, self.username)
            os.chmod(password_file_old, stat.S_IREAD | stat.S_IWRITE)
        if existing_password is not None:
            with open(password_file_old, 'w') as f:
                f.write(existing_password)
                f.truncate()
                f.close()
            shutil.chown(password_file_old, self.username, self.username)
            os.chmod(password_file_old, stat.S_IREAD | stat.S_IWRITE)
        with open(password_file, 'w') as f:
            f.write(password)
            f.truncate()
            f.close()
        if not password_file_existed:
            shutil.chown(password_file, self.username, self.username)
            os.chmod(password_file, stat.S_IREAD | stat.S_IWRITE)

    def download_directory(self):
        return self.home_directory() + 'Downloads/'

    def etc_directory(self):
        return self.home_directory() + 'etc/'

    def home_directory(self):
        return '/home/' + self.username + '/'

    def mongo_database(self):
        return 'user:' + self.username

    def lockfile_directory(self):
        return self.working_directory()

    def working_directory(self):
        return '/var/run/' + USER + '/apps/' + self.username + '/'
