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
from os import listdir
from os.path import isdir, join
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


def remove_invalid_users():
    """
    Remove any invalid users from pgadmin user entries.
    This includes pgadmin user's "pgpass" file.
    """
    pgadmin_db = (__salt__['pillar.get']('pgadmin_lib_path')
                  + '/pgadmin4.db')
    if not os.path.isfile(pgadmin_db):
        return True

    # Temporary file write for development
    f = open("/tmp/pgadmin.txt", "a")
    # f.write()

    # Get some needed data
    pgadmin_default_user = __salt__['pillar.get']('pgadmin_default_user')
    pgadmin_storage_path = __salt__['pillar.get']('pgadmin_storage_path')
    users = __salt__['pillar.get']('users')
    f.write(pgadmin_default_user)
    f.write(str(users))

    # Remove any unneeded storage directories
    directories = [d for d in listdir(pgadmin_storage_path)
                   if isdir(join(pgadmin_storage_path, d))]
    f.write(str(directories))

    f.close()
    # ALEX
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
           Table structure (required columns):
             id INTEGER NOT NULL
               Auto generated primary key
             email VARCHAR(256)
             password VARCHAR
               Double-hash password using SECURITY_PASSWORD_SALT
             active BOOLEAN NOT NULL
             masterpass_check VARCHAR(256)
               106-character string (NEEDS RESEARCH)
             username VARCHAR(256) NOT NULL
             auth_source VARCHAR(256) DEFAULT 'internal' NOT NULL
             fs_uniquifier VARCHAR NOT NULL
               32-character random string
           Sample entry (one column per line):
             1,
             pgadmin@laikasden.com,
             <OMITTED FOR LENGTH>
             1
             <OMITTED FOR LENGTH>
             pgadmin@laikasden.com
             internal
             ca69ee8cfef348b6a3870dfe05d9bc89

        b. roles_users: pgadmin user should have admin role; user role
        for all others.
           Table structure:
             user_id INTEGER
               FOREIGN KEY(user_id) REFERENCES user (id)
             role_id INTEGER
               FOREIGN KEY(role_id) REFERENCES role (id)
           "role" table has these entries:
             (1, 'Administrator', 'pgAdmin Administrator Role')
             (2, 'User', 'pgAdmin User Role')
           Sample entry (one column per line):
             1
             1
           Notes:
             - One role per user
             - All users are of type "User" except for the admin user.

        c. servergroup: Server UI group entries for all users.
           Table structure:
             id INTEGER NOT NULL
               Auto generated primary key
             user_id INTEGER NOT NULL
               FOREIGN KEY(user_id) REFERENCES user (id)
             name VARCHAR(128) NOT NULL
           Sample entry (one column per line):
             1
             1
             Interface
           Notes:
             - Create "interface" group for front-end databases

        d. server: Admin user entries for local postgres server and
        databases.
           Table structure (required columns):
             id INTEGER NOT NULL
               Auto generated primary key
             user_id INTEGER NOT NULL
             servergroup_id INTEGER NOT NULL
             name VARCHAR(128) NOT NULL
             host VARCHAR(128)
             port INTEGER
             maintenance_db VARCHAR(64)
             username VARCHAR(64)
             comment VARCHAR(1024)
             db_res VARCHAR
             shared BOOLEAN,
             connection_params JSON
             FOREIGN KEY(user_id) REFERENCES user (id)
             FOREIGN KEY(servergroup_id) REFERENCES servergroup (id)
           Sample entry (one column per line):
             1
             1
             1
             Django Application Data
             192.168.1.179
             5432
             app_data
             uwsgi
             Django interface server
             app_data
             1
             {"sslmode": "require",
              "passfile": "/pgpass",
              "connect_timeout": 10}
           Notes:
             - Add one entry for each front end database

        e. sharedserver: Non-admin user entries for local postgres server and
        databases (pointing back to "server")
           Table structure (required columns):
             id INTEGER NOT NULL
               Auto generated primary key
             user_id INTEGER NOT NULL
             server_owner VARCHAR(64)
             servergroup_id INTEGER NOT NULL
             name VARCHAR(128) NOT NULL
             host VARCHAR(128)
             port INTEGER
             maintenance_db VARCHAR(64)
             username VARCHAR(64)
             shared BOOLEAN NOT NULL
             osid INTEGER
             connection_params JSON
             FOREIGN KEY(servergroup_id) REFERENCES servergroup (id)
             FOREIGN KEY(user_id) REFERENCES user (id)
           Sample entry (one column per line):
             1
             2
             pgadmin@laikasden.com
             1
             Django Application Data
             192.168.1.179
             5432
             app_data
             uwsgi
             1
             1
             {"sslmode": "require",
              "passfile": "/pgpass",
              "connect_timeout": 10}

    The admin user will always exist since it is initialized by the
    docker start-up. However, other table data won't exist at start-up, while
    the admin user password needs to be rotated.

    The rules for the update are as follows:

    1. User doesn't exist
       - Add appropriate entries to database tables following the table order
       shown above.
       - On initial entry of non-admin user, the password is randomly
       generated and won't be saved. This will necessitate some password
       change utility on the control panel that allows the user to reset
       his/her password, and this utility will need to hook into
       the padmin database to reset the password there as well. See the
       utility function above, "set_pgadmin_password".
    2. User exists, admin user
       - Verify all entries exist for all tables
       - Rotate user password
       - Put copy of password in admin's directory, if exists.
    3. User exists, non-admin user
       - Verify all entries exist for all tables

    """
    pgadmin_db = (__salt__['pillar.get']('pgadmin_lib_path')
                  + '/pgadmin4.db')
    connection = sqlite3.connect(pgadmin_db)
    cursor = connection.cursor()

    # Temporary file write for development
    f = open("/tmp/pgadmin.txt", "a")
    # Check if user is in database
    query = ("select * from user where email = '{}'"
             .format(email_address))
    f.write(query)
    cursor.execute(query)
    user_entry = cursor.fetchone()[0]
    f.write(str(user_entry))

    f.close()
    return True
