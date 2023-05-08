# -*- coding: utf-8 -*-

'''
Tools for managing cross-server credentials
'''

import os
import subprocess

from olympus import RESTAPI_SERVICE, User


def backend():
    frontend_user = __salt__['pillar.get']('frontend-user')  # noqa: F403
    passphrase = __salt__['data.get']('frontend_db_key')  # noqa: F403
    server = __grains__['server']  # noqa: F403
    services = None
    if (passphrase is not None and server is not None):
        key = 'servers:' + server + ':services'
        services = __salt__['pillar.get'](key)  # noqa: F403
        if 'backend' in services:
            cmd = ("sudo -u postgres psql -c \"ALTER USER " +
                   frontend_user +
                   " ENCRYPTED PASSWORD '" +
                   passphrase +
                   "';\"")
            subprocess.check_call(cmd, shell=True)
        if 'frontend' not in services:
            __salt__['data.pop']('frontend_db_key')  # noqa: F403
    return True


def rotate_restapi_password_file(username, tmp_file_name):
    server = __grains__['server']  # noqa: F403
    staff_key = 'users:' + username + ':is_staff'
    is_staff = __salt__['pillar.get'](staff_key)  # noqa: F403
    servers_key = 'users:' + username + ':server'
    user_servers = __salt__['pillar.get'](servers_key)  # noqa: F403
    if not user_servers:
        user_servers = []
    if is_staff:
        pass
    elif user_servers is False:
        return True
    elif server not in user_servers:
        return True
    with open(tmp_file_name, 'r') as f:
        new_password = f.readline().rstrip()
    user = User(username)
    user.rotate_service_password_file(RESTAPI_SERVICE, new_password)
    os.remove(tmp_file_name)
    return True


def shared_database():
    frontend_user = __salt__['pillar.get']('frontend-user')  # noqa: F403
    passphrase = __salt__['data.get']('frontend_db_key')  # noqa: F403
    server = __grains__['server']  # noqa: F403
    services = None
    if (passphrase is not None and server is not None):
        key = 'servers:' + server + ':services'
        services = __salt__['pillar.get'](key)  # noqa: F403
        delete_minion_data = False
        if 'backend' in services:
            # Is database running?
            cmd = "ps -A | grep postgres | wc -l"
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 text=True)
            backend_processes = p.communicate()[0].strip("\n")
            if int(backend_processes) > 0:
                # Does frontend user exist?
                cmd = ("sudo -u postgres psql -tAc " +
                       "\"SELECT rolname FROM pg_roles WHERE rolname='" +
                       frontend_user +
                       "'\"")
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     text=True)
                output = p.communicate()
                rolname = output[0].split("\n")[-2]
                if rolname == frontend_user:
                    # Update frontend user password
                    cmd = ("sudo -u postgres psql -c " +
                           "\"ALTER USER " +
                           frontend_user +
                           " ENCRYPTED PASSWORD '" +
                           passphrase +
                           "';\"")
                    subprocess.check_call(cmd, shell=True)
                    delete_minion_data = True
        if 'frontend' in services:
            delete_minion_data = False
            frontend_credential_file = \
                '/srv/www/django/interface/settings_local.py'
            if os.path.isfile(frontend_credential_file):
                # If frontend configuration exists, update password
                cmd = ("perl -i -pe " +
                       "'s/('\\''PASSWORD'\\''\\:\\s+'\\'')(.*?)('\\'')/$1" +
                       passphrase +
                       "$3/g' " +
                       frontend_credential_file)
                subprocess.check_call(cmd, shell=True)
                # If dev frontend web service is running, restart
                cmd = "ps -A | grep runserver | wc -l"
                p = subprocess.Popen(cmd,
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     text=True)
                frontend_dev_processes = p.communicate()[0].strip("\n")
                if int(frontend_dev_processes) > 0:
                    cmd = "/usr/local/bin/killserver.sh"
                    subprocess.check_call(cmd, shell=True)
                    cmd = "/usr/local/bin/startserver.py"
                    subprocess.check_call(cmd, shell=True)
                else:
                    # If frontend web service is running, restart
                    cmd = "ps -A | grep uwsgi | wc -l"
                    p = subprocess.Popen(cmd,
                                         shell=True,
                                         stdout=subprocess.PIPE,
                                         text=True)
                    frontend_processes = p.communicate()[0].strip("\n")
                    if int(frontend_processes) > 0:
                        cmd = "service uwsgi restart"
                        subprocess.check_call(cmd, shell=True)
        if delete_minion_data is True:
            __salt__['data.pop']('frontend_db_key')  # noqa: F403
    return True
