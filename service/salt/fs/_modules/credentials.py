# -*- coding: utf-8 -*-

'''
Tools for managing cross-server credentials
'''

import os, subprocess

def database():
    credential_file = __salt__['pillar.get']('credential_dir') + '/' + __salt__['pillar.get']('db_credential_file')
    exclude_server = __salt__['pillar.get']('db_credential_exclude_server_type')
    frontend_user = __salt__['pillar.get']('frontend-user')
    server = __grains__['server']
    services = None
    if (server is not None and server != exclude_server):
        key = server + ':services'
        passphrase = None
        services = __salt__['pillar.get'](key)
        try:
            with open(credential_file) as f:
                passphrase = f.readlines()[0].strip()
        except:
            raise
        updated = False
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
                    updated = True
        if 'frontend' in services:
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
                    updated = True
        if updated is True:
            os.renove(credential_file)
    return True
