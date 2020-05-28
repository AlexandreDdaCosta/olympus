# -*- coding: utf-8 -*-

'''
Manage data backup and restoration
'''

def ping():
    frontend_user = __salt__['pillar.get']('frontend-user')
    passphrase = __salt__['data.get']('frontend_db_key')
    server = __grains__['server']
    services = None
    return True
