# -*- coding: utf-8 -*-

'''
Tools for managing cross-server credentials
'''

import os, subprocess

def database():
    credential_file = __salt__['pillar.get']('credential_dir') + '/' + __salt__['pillar.get']('db_credential_file')
    exclude_server = __salt__['pillar.get']('db_credential_exclude_server_type')
    server = __grains__['server']
    services = None
    if (server is not None and server != exclude_server):
        key = server + ':services'
        passphrase = None
        services = __salt__['pillar.get'](key)
        try:
            with open(credential_file) as f:
                passphrase = f.readlines()
        except:
            raise
        if 'backend' in services:
            process = subprocess.Popen(['ps','-A','|','grep','postgres','|','wc','-l'], stdout=subprocess.PIPE)
            output = process.communicate()[0]
            return output
            # If backend user exists, update password
            return 'backend'
        if 'frontend' in services:
            # If frontend configuration exists, update password
            # If frontend web service is running, restart
            return 'frontend'
    return True
