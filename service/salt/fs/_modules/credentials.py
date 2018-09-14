# -*- coding: utf-8 -*-

'''
Tools for managing cross-server credentials
'''

import os

def database():
    credential_file = __salt__['pillar.get']('credential_dir') + '/' + __salt__['pillar.get']('db_credential_file')
    exclude_server = __salt__['pillar.get']('db_credential_exclude_server_type')
    server = __grains__['server']
    services = None
    if (server is not None and server != exclude_server):
        key = server + ':services'
        services = __salt__['pillar.get'](key)
        try:
            with open(credential_file) as f:
                passphrase = f.readlines()
        except:
            raise
        if 'backend' in services:
            return 'backend'
        if 'frontend' == services:
            return 'frontend'
    '''
    try:
        os.remove(credential_file)
    except:
        raise
    '''
    return services
