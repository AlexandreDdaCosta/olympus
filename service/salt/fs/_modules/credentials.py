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
        if 'backend' in services:
            # Is database running?
            cmd = "ps -A | grep postgres | wc -l"
            p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            database_processes = p.communicate()[0].strip("\n")
            if int(database_processes) > 0:
                # Does frontend user exist?
                cmd = "sudo -u postgres psql -tAc \"SELECT rolname FROM pg_roles WHERE rolname='" + frontend_user + "'\""
                p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                output = p.communicate()
                last = output[0].split("\n")
                return last[0]
                # Update frontend user password
                cmd = "sudo -u postgres psql -c \"ALTER USER " + frontend_user  + " ENCRYPTED PASSWORD '" + passphrase  + "';\""
                p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if 'frontend' in services:
            # If frontend configuration exists, update password
            # If frontend web service is running, restart
            return 'frontend'
    return True
