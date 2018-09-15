# -*- coding: utf-8 -*-

'''
Tools for managing cross-server credentials
'''

import os, subprocess

def database():
    credential_file = __salt__['pillar.get']('credential_dir') + '/' + __salt__['pillar.get']('db_credential_file')
    exclude_server = __salt__['pillar.get']('db_credential_exclude_server_type')
    frontend_user = __salt__['pillar.get']('frontend_user')
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
            # Check for running database
            cmd = "ps -A | grep postgres | wc -l"
            p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            database_processes = p.communicate()[0].strip("\n")
            return database_processes
            if int(database_processes) > 0:
                # Does frontend user exist?
                cmd = "sudo -u postgres psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='" + frontend_user + "'\" | grep -q 1"
                p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                output = p.communicate()[-1].strip()
                return output
                # Update frontend user password
        if 'frontend' in services:
            # If frontend configuration exists, update password
            # If frontend web service is running, restart
            return 'frontend'
    return True
