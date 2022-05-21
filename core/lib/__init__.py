# Systemwide constants

# Default library user and settings

USER = 'olympus'
def USER_ETC(user=USER):
    return '/home/' + user + '/etc/'
def USER_HOME(user=USER):
    return '/home/' + user + '/'
def DOWNLOAD_DIR(user=USER):
    return USER_HOME(user) + 'Downloads/'
def LOCKFILE_DIR(user=USER):
    return '/var/run/'+USER+'/apps/'+user+'/'
def WORKING_DIR(user=USER):
    return '/var/run/'+USER+'/apps/'+user+'/'

# Backend

MONGO_ADMIN_USERNAME = 'mongodb'
MONGO_URL = 'mongodb://localhost:27017/'
def MONGO_USER_DATABASE(user):
    return 'user_' + user
RESTAPI_RUN_USERNAME = 'node'

# Password hashing via argon2

ARGON2_CONFIG = { "memory_cost": 64*1024, "parallelism": 1, "salt_bytes": 16, "time_cost": 3 }

# Password files

def RESTAPI_USER_PASSWORD_FILE(user):
    return USER_ETC(user) + 'restapi_password'
def RESTAPI_USER_OLD_PASSWORD_FILE(user):
    return USER_ETC(user) + 'mongodb_password.old'
