# -*- coding: utf-8 -*-

'''
Tools for managing pgadmin.
Includes SQLite database, credentials, pgpass files
'''

import hashlib
import hmac
import os
import re
import sqlite3
import subprocess

from base64 import b64encode
from passlib.hash import pbkdf2_sha512
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    __grains__: Any = None
    __salt__: Any = None


def find_update_pgpass():
    """
    For all front end databases, updates the password entry in each
    pgadmin user's "pgpass" file.
    """
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


def pgpass_frontend_password(file_name):
    """
    Updates a user's pgpass file with updated front end password
    """
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
    """
    Updates the main pgadmin password entry for a user.
    Currently, this function exists as a placeholder.
    The logic embedded here will be incorporated into a more comprehensive
    function designed to populate SQLite entries for all pgadmin users.
    """
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


def pgadmin_db_user(username, email_address):
    """
    Populates and updates user configuration entries in pgadmin's
    SQLite database.
    Will need to touch these tables:
        a. user: Basic user information, including password
        b. roles_users: pgadmin user should have admin role; user role
        for all others.
        c. server: pgadmin user entries for local postgres server and
        databases.
        d. sharedserver: Entries for all non-pgadmin users (pointing
        back to "server")
        e. servergroup: Server UI group entries for all users.
    """
    pgadmin_db = (__salt__['pillar.get']('pgadmin_lib_path')
                  + '/pgadmin4.db')
    connection = sqlite3.connect(pgadmin_db)
    cursor = connection.cursor()

    f = open("/tmp/pgadmin.txt", "a")
    # Check if user is in database
    query = ("select * from user where email = '{}'"
             .format(email_address))
    cursor.execute(query)
    user_entry = cursor.fetchone()[0]
    #f.write(str(user_entry))

    f.close()
    return True
