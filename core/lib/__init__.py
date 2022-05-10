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
def MONGO_USER_PASSWORD_FILE(user=MONGO_ADMIN_USERNAME):
    return USER_ETC(user) + 'mongodb_password'

