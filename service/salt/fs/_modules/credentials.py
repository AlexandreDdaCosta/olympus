# -*- coding: utf-8 -*-

'''
Tools for managing cross-server credentials
'''

import os, subprocess

def backend():
    frontend_user = __salt__['pillar.get']('frontend-user')
    passphrase = __salt__['data.get']('frontend_db_key')
    server = __grains__['server']
    services = None
    if (passphrase is not None and server is not None):
        key = server + ':services'
        services = __salt__['pillar.get'](key)
        if 'backend' in services:
            cmd = "sudo -u postgres psql -c \"ALTER USER " + frontend_user  + " ENCRYPTED PASSWORD '" + passphrase  + "';\""
            p = subprocess.check_call(cmd,shell=True)
        if 'frontend' not in services:
            __salt__['data.pop']('frontend_db_key')
    return True

# ALEX pillar for conf file; restart dev server if running instead of uwsgi
def shared_database():
    frontend_user = __salt__['pillar.get']('frontend-user')
    passphrase = __salt__['data.get']('frontend_db_key')
    server = __grains__['server']
    services = None
    if (passphrase is not None and server is not None):
        key = server + ':services'
        services = __salt__['pillar.get'](key)
        delete_minion_data = False
        if 'backend' in services:
            # Is database running?
            cmd = "ps -A | grep postgres | wc -l"
            p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
            backend_processes = p.communicate()[0].strip("\n")
            if int(backend_processes) > 0:
                # Does frontend user exist?
                cmd = "sudo -u postgres psql -tAc \"SELECT rolname FROM pg_roles WHERE rolname='" + frontend_user + "'\""
                p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
                output = p.communicate()
                rolname = output[0].split("\n")[-2]
                if rolname == frontend_user:
                    # Update frontend user password
                    cmd = "sudo -u postgres psql -c \"ALTER USER " + frontend_user  + " ENCRYPTED PASSWORD '" + passphrase  + "';\""
                    p = subprocess.check_call(cmd,shell=True)
                    delete_minion_data = True
        if 'frontend' in services:
            delete_minion_data = False
            frontend_credential_file = '/srv/www/django/interface/settings_local.py'
            if os.path.isfile(frontend_credential_file):
                # If frontend configuration exists, update password
                cmd = "perl -i -pe 's/('\\''PASSWORD'\\''\\:\\s+'\\'')(.*?)('\\'')/$1" + passphrase + "$3/g' " + frontend_credential_file
                p = subprocess.check_call(cmd,shell=True)
                # If frontend web service is running, restart
                cmd = "ps -A | grep uwsgi | wc -l"
                p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
                frontend_processes = p.communicate()[0].strip("\n")
                if int(frontend_processes) > 0:
                    cmd = "service uwsgi restart"
                    p = subprocess.check_call(cmd,shell=True)
        if delete_minion_data is True:
            __salt__['data.pop']('frontend_db_key')
    return True
