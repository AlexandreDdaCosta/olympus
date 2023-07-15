# -*- coding: utf-8 -*-

'''
Tools for managing cross-server and other credentials
'''

import grp
import os
import pwd
import subprocess

from shutil import copyfile
from typing import Any, TYPE_CHECKING

from olympus import RESTAPI_SERVICE, User

if TYPE_CHECKING:
    __grains__: Any = None
    __salt__: Any = None


def frontend_db_password():
    frontend_password_file_name = \
        __salt__['pillar.get']('frontend_password_file_name')
    frontend_credential_file = \
        __salt__['pillar.get']('frontend_conf_file_name')
    if (os.path.isfile(frontend_credential_file)
            and os.path.isfile(frontend_password_file_name)):
        # If frontend configuration exists and password file exists,
        # make sure the config file password matches that of the
        # password file
        frontend_password_file = open(frontend_password_file_name)
        passphrase = frontend_password_file.read().strip("\n")
        frontend_password_file.close()
        cmd = ("perl -i -pe " +
               "'s/('\\''PASSWORD'\\''\\:\\s+'\\'')(.*?)('\\'')/${1}" +
               passphrase +
               "${3}/g' " +
               frontend_credential_file)
        subprocess.check_call(cmd, shell=True)
    return True


def interface_backend():
    frontend_user = __salt__['pillar.get']('frontend_user')
    passphrase = __salt__['data.get']('frontend_db_key')
    server = __grains__['server']
    services = None
    if (passphrase is not None and server is not None):
        key = 'servers:' + server + ':services'
        services = __salt__['pillar.get'](key)
        if 'database' in services:
            cmd = ("sudo -u postgres psql -c \"ALTER USER " +
                   frontend_user +
                   " ENCRYPTED PASSWORD '" +
                   passphrase +
                   "';\"")
            subprocess.check_call(cmd, shell=True)
        if 'frontend' not in services:
            __salt__['data.pop']('frontend_db_key')
    return True


def rotate_restapi_password_file(username, tmp_file_name):
    server = __grains__['server']
    staff_key = 'users:' + username + ':is_staff'
    is_staff = __salt__['pillar.get'](staff_key)
    servers_key = 'users:' + username + ':server'
    user_servers = __salt__['pillar.get'](servers_key)
    if not user_servers:
        user_servers = []
    if is_staff:
        pass
    elif user_servers is False:
        return True
    elif server not in user_servers:
        return True
    user = User(username)
    if not os.path.isdir(user.etc_directory()):
        return True
    with open(tmp_file_name, 'r') as f:
        new_password = f.readline().rstrip()
    user.rotate_service_password_file(RESTAPI_SERVICE, new_password)
    os.remove(tmp_file_name)
    return True


def shared_database():
    frontend_password_file_name = \
        __salt__['pillar.get']('frontend_password_file_name')
    frontend_user = __salt__['pillar.get']('frontend_user')
    passphrase = __salt__['data.get']('frontend_db_key')
    server = __grains__['server']
    web_daemon = __salt__['pillar.get']('web_daemon')
    bin_path = __salt__['pillar.get']('bin_path_scripts')
    kill_script = __salt__['pillar.get']('dev_kill_script')
    start_script = __salt__['pillar.get']('dev_start_script')
    services = None
    if (passphrase is not None and server is not None):
        key = 'servers:' + server + ':services'
        services = __salt__['pillar.get'](key)
        delete_minion_data = False
        # Back up password file if it exists
        if os.path.isfile(frontend_password_file_name):
            copyfile(frontend_password_file_name,
                     frontend_password_file_name + '.old')
        # Write updated passphrase into password file
        with open(frontend_password_file_name, "w") as passfile:
            passfile.write(passphrase)
        os.chmod(frontend_password_file_name, 0o600)
        uid = pwd.getpwnam(frontend_user).pw_uid
        gid = grp.getgrnam(frontend_user).gr_gid
        os.chown(frontend_password_file_name, uid, gid)
        if 'database' in services:
            # Is database running?
            cmd = "ps -A | grep postgres | wc -l"
            p = subprocess.Popen(cmd,
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 text=True)
            database_processes = p.communicate()[0].strip("\n")
            if int(database_processes) > 0:
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
                __salt__['pillar.get']('frontend_conf_file_name')
            if os.path.isfile(frontend_credential_file):
                # If frontend configuration exists, update password
                cmd = ("perl -i -pe " +
                       "'s/('\\''PASSWORD'\\''\\:\\s+'\\'')(.*?)('\\'')/${1}" +
                       passphrase +
                       "${3}/g' " +
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
                    cmd = bin_path + "/" + kill_script
                    subprocess.check_call(cmd, shell=True)
                    cmd = bin_path + "/" + start_script
                    subprocess.check_call(cmd, shell=True)
                else:
                    # If frontend web service is running, restart
                    cmd = "ps -A | grep " + web_daemon + " | wc -l"
                    p = subprocess.Popen(cmd,
                                         shell=True,
                                         stdout=subprocess.PIPE,
                                         text=True)
                    frontend_processes = p.communicate()[0].strip("\n")
                    if int(frontend_processes) > 0:
                        cmd = "service " + web_daemon + " restart"
                        subprocess.check_call(cmd, shell=True)
        if delete_minion_data is True:
            __salt__['data.pop']('frontend_db_key')
    return True
