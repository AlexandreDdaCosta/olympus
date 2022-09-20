# Core constants and classes

import os, re, shutil, stat

from os.path import isfile

USER = 'olympus'

ARGON2_CONFIG = { "memory_cost": 64*1024, "parallelism": 1, "salt_bytes": 16, "time_cost": 3 }
CLIENT_CERT='/etc/ssl/localcerts/client-key-crt.pem'
MONGODB_SERVICE = 'mongodb'
REDIS_SERVICE = 'redis'
RESTAPI_RUN_USERNAME = 'node'
RESTAPI_SERVICE = 'restapi'

PASSWORD_ENABLED_SERVICES = [ MONGODB_SERVICE, REDIS_SERVICE, RESTAPI_SERVICE ]

class Series(object):

    # A series of objects

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

    def sort(self,attribute,reverse=False):
        # Sort the series by an object attribute
        if self.series is not None:
            self.series = sorted(self.series, key=lambda s: getattr(s,attribute), reverse=reverse)

class String(object):

    # Some useful string methods

    def __init__(self):
        pass

    def pascal_case_to_underscore(self,string):
        # First line deals with whitespace
        string = re.sub(r'\b[A-Za-z0-9]', lambda m: m.group().upper().replace("\b",""), str(string))
        return re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', r'_\1', string).lower().strip('_')

class User():

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
