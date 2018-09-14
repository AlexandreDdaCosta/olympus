# -*- coding: utf-8 -*-

'''
Tools for managing cross-server credentials
'''

import json

def database():
    credential_file = __salt__['pillar.get']('db_credential_file', None)
    exclude_server = __salt__['pillar.get']('db_credential_exclude_server_type', None)
    credential_directory = __salt__['pillar.get']('credential_directory', None)
    server = __grains__['server']

    if (server is not None and server ne exclude_server)
        pass
    return credential_file + ' ' + exclude_server + ' ' + server
