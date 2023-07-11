# -*- coding: utf-8 -*-

'''
Tools for managing cross-server and other credentials
'''

import grp
import hashlib
import hmac
import os
import pwd
import re
import sqlite3
import subprocess

from base64 import b64encode
from passlib.hash import pbkdf2_sha512
from shutil import copyfile
from typing import Any, TYPE_CHECKING

from olympus import RESTAPI_SERVICE, User

if TYPE_CHECKING:
    __grains__: Any = None
    __salt__: Any = None


def find_update_pgpass():
    frontend_password_file_old_name = \
        __salt__['pillar.get']('frontend_password_file_name') + '.old'
    if not os.path.isfile(frontend_password_file_old_name):
        return True
    frontend_password_file_old = open(frontend_password_file_old_name)
    old_passphrase = frontend_password_file_old.read().strip("\n")
    frontend_password_file_old.close()
    frontend_password_file_name = \
        __salt__['pillar.get']('frontend_password_file_name')
    frontend_password_file = open(frontend_password_file_name)
    new_passphrase = frontend_password_file.read().strip("\n")
    frontend_password_file.close()
    pgadmin_storage_path = \
        __salt__['pillar.get']('pgadmin_storage_path')
    for root, dirs, files in os.walk(pgadmin_storage_path):  # pyright: ignore
        if 'pgpass' in files:
            pgpass_file_name = os.path.join(root, 'pgpass')
            cmd = ("perl -i -pe " +
                   "'s/" +
                   old_passphrase +
                   "/" +
                   new_passphrase +
                   "/g' " +
                   pgpass_file_name)
            subprocess.check_call(cmd, shell=True)
    return True


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


def pgpass_frontend_password(file_name):
    if os.path.isfile(file_name):
        frontend_password_file_name = \
            __salt__['pillar.get']('frontend_password_file_name')
        passphrase = None
        if os.path.isfile(frontend_password_file_name):
            frontend_password_file = open(frontend_password_file_name)
            passphrase = frontend_password_file.read().strip("\n")
            frontend_password_file.close()
        if passphrase is None:
            return True
        frontend_databases = \
            __salt__['pillar.get']('frontend_databases')
        # Clean up pgpass file represented by file_name
        # 1. Remove empty lines
        # 2. Swap out password for all lines that contain a frontend entry
        pgpass_file = open(file_name)
        pgpass_file_contents = pgpass_file.read().strip("\n")
        pgpass_file.close()
        new_contents = ''
        lines = pgpass_file_contents.splitlines()
        for line in lines:
            result = re.match(r'\S', line)
            if not result:
                continue
            db_matched = False
            for db in frontend_databases:
                database = frontend_databases[db]['name']
                user = frontend_databases[db]['user']
                pattern = ('^\\S+:\\S+:' +
                           database +
                           ':' +
                           user +
                           ':\\S+$')
                result = re.match(pattern, line)
                if not result:
                    continue
                db_matched = True
                updated_line = re.sub(r'^(\S+:\S+:\S+:\S+:)(\S+)$',
                                      r'\1' + passphrase,
                                      line)
                new_contents += updated_line
            if not db_matched:
                new_contents += line
            new_contents += "\n"
        with open(file_name, "w") as updated_pgpass_file:
            updated_pgpass_file.write(new_contents)
    return True


def set_pgadmin_password(user_email, new_password):
    pgadmin_db = (__salt__['pillar.get']('pgadmin_lib_path')
                  + '/pgadmin4.db')
    connection = sqlite3.connect(pgadmin_db)
    cursor = connection.cursor()

    # Get SECURITY_PASSWORD_SALT from the pgadmin configuration database

    query = "select value from keys where name = 'SECURITY_PASSWORD_SALT'"
    cursor.execute(query)
    security_password_salt = cursor.fetchone()[0]

    # Get old user password hash

    query = "select password from user where email = '{}'".format(user_email)
    cursor.execute(query)
    old_user_hash = cursor.fetchone()[0]
    (empty, algorithm, rounds, salt, old_password_hash) = \
        old_user_hash.split("$")
    del empty, salt, old_password_hash
    if algorithm != 'pbkdf2-sha512':
        raise Exception('Can\'t update password; algorithm has changed.')

    # Create new password data

    new_salt = os.urandom(16)
    h = hmac.new(str.encode(security_password_salt),
                 new_password.encode("utf-8"),
                 hashlib.sha512)
    new_user_hash = pbkdf2_sha512.hash(b64encode(h.digest()),
                                       rounds=rounds,
                                       salt=new_salt)

    # Update user password hash

    query = "update user set password = '{}' where email = '{}'".format(
        new_user_hash,
        user_email)
    cursor.execute(query)
    connection.commit()
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
