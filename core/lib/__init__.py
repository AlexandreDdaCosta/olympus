# Systemwide constants

# Default library user and settings

USER = 'olympus'
def USER_HOME(user=USER):
    return '/home/' + user + '/'
def DOWNLOAD_DIR(user=USER):
    return USER_HOME(user) + 'Downloads/'
def LOCKFILE_DIR(user=USER):
    return '/var/run/'+USER+'/apps/'+user+'/'
def WORKING_DIR(user=USER):
    return '/var/run/'+USER+'/apps/'+user+'/'

# SSL connection files

CAFILE = '/usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt'
CERTFILE = '/etc/ssl/localcerts/client-crt.pem'
CERTKEYFILE = '/etc/ssl/localcerts/client-key-crt.pem'
KEYFILE = '/etc/ssl/localcerts/client-key.pem'

# Backend

MONGO_URL = 'mongodb://localhost:27017/?tls=true';
