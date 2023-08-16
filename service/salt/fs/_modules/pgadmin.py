# -*- coding: utf-8 -*-

'''
Tools for managing pgadmin.
Includes SQLite database, credentials, pgpass files
'''

import grp
import hashlib
import hmac
import os
import pwd
import random
import re
import shutil
import sqlite3
import string
import subprocess

from base64 import b64encode
from os import listdir
from os.path import isdir, isfile, join
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


def remove_invalid_users(): # noqa
    """
    Remove any invalid users from pgadmin user entries.
    This includes pgadmin user's "pgpass" file.
    """
    pgadmin_db = (__salt__['pillar.get']('pgadmin_lib_path')
                  + '/pgadmin4.db')
    if not os.path.isfile(pgadmin_db):
        return True

    # Get some needed data
    pgadmin_default_user = __salt__['pillar.get']('pgadmin_default_user')
    pgadmin_storage_path = __salt__['pillar.get']('pgadmin_storage_path')
    users = __salt__['pillar.get']('users')

    # Remove any unneeded storage directories
    directories = [d for d in listdir(pgadmin_storage_path)
                   if isdir(join(pgadmin_storage_path, d))]
    for directory in directories:
        valid_user = False
        for user in users:
            if 'email_address' in users[user]:
                email_address = users[user]['email_address']
                email_address = email_address.replace('@', '_')
                if email_address == directory:
                    if user == pgadmin_default_user:
                        valid_user = True
                    elif 'is_staff' in users[user] and users[user]['is_staff']:
                        valid_user = True
                    break
                else:
                    continue
            else:
                continue
        if not valid_user:
            shutil.rmtree(pgadmin_storage_path + "/" + directory)

    # Remove any invalid user entries

    # Close all sessions
    pgadmin_sessions_path = __salt__['pillar.get']('pgadmin_sessions_path')
    session_files = [f for f in listdir(pgadmin_sessions_path)
                     if isfile(join(pgadmin_sessions_path, f))]
    for file in session_files:
        os.remove(pgadmin_sessions_path + "/" + file)

    # Retrieve and check database entries for all current users
    connection = sqlite3.connect("/var/lib/pgadmin/pgadmin4.db")
    cursor = connection.cursor()
    delete_users = []
    query = "select * from user"
    for row in cursor.execute(query):
        valid_user = False
        user_id = row[0]
        user_name = row[1]
        for user in users:
            if ('email_address' in users[user] and
                    user_name == users[user]['email_address']):
                if user == pgadmin_default_user:
                    valid_user = True
                    break
                if 'is_staff' in users[user] and users[user]['is_staff']:
                    valid_user = True
                    break
        if valid_user is False:
            delete_users.append(user_id)

    # Delete bad users from database
    for user_id in delete_users:
        query = "delete from roles_users where user_id = {0}".format(user_id)
        cursor.execute(query)
        query = "delete from sharedserver where user_id = {0}".format(user_id)
        cursor.execute(query)
        query = "delete from server where user_id = {0}".format(user_id)
        cursor.execute(query)
        query = "delete from servergroup where user_id = {0}".format(user_id)
        cursor.execute(query)
        query = "delete from user where id = {0}".format(user_id)
        cursor.execute(query)
        connection.commit()

    return True


def set_pgadmin_password(user_email, new_password):
    """
    Updates the main pgadmin password entry for a user.
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
    f = open("/tmp/pgadmin.txt", "a", buffering=1)
    f.write("HASHVAL\n\n")
    f.write(str(user_email) + "\n\n")
    f.write(str(old_user_hash) + "\n\n")
    f.close()
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


def pgadmin_db_user(): # noqa: C901
    """
    Populates and updates users' configuration entries in pgadmin's
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

    1. Remove all of the following user data for all users:
       1a. roles_users
       1b. sharedserver
       1c. server
       1d. servergroup
    2. Write user entries (starting with admin user)
       2a. User exists
           2a1. Admin user
                2a1a. Write entries for all missing tables
                2a1b. Rotate user password
                2a1c. Put copy of password in admin's directory, if exists.
           2a2. User exists, non-admin user
                2a2a. Write entries for all missing tables
       2b. User doesn't exist
           2b1. Add main user entry
           Then follow 2a1a and 2a2a.
           For admin user, follow 2a1c.

    On initial entry of non-admin user, the password is randomly generated and
    won't be saved. This will necessitate some password change utility on the
    control panel that allows the user to reset his/her password, and this
    utility will need to hook into the pgadmin database to reset the password
    there as well. See the utility function above, "set_pgadmin_password".
    """

    pgadmin_db = (__salt__['pillar.get']('pgadmin_lib_path')
                  + '/pgadmin4.db')
    pgadmin_default_user = __salt__['pillar.get']('pgadmin_default_user')
    pgadmin_password_file = \
        ('/home/' + pgadmin_default_user + '/etc/' +
         __salt__['pillar.get']('pgadmin_password_file_name'))
    frontend_databases = __salt__['pillar.get']('frontend_databases')

    frontend_server_groupname = 'Interface'

    users = __salt__['pillar.get']('users')
    connection = sqlite3.connect(pgadmin_db)
    cursor = connection.cursor()

    # 1.

    # 1a.
    query = "delete from roles_users"
    cursor.execute(query)
    # 1b.
    query = "delete from sharedserver"
    cursor.execute(query)
    # 1c.
    query = "delete from server"
    cursor.execute(query)
    # 1d.
    query = "delete from servergroup"
    cursor.execute(query)
    connection.commit()

    # Get preliminary data
    f = open("/tmp/pgadmin.txt", "a", buffering=1)
    # List of users in pillar to add to pgadmin user records
    admin_user_email = None
    pgadmin_user_emails = []
    for user in users:
        if 'email_address' not in users[user]:
            continue
        if user == pgadmin_default_user:
            admin_user_email = users[user]['email_address']
        elif 'is_staff' in users[user] and users[user]['is_staff']:
            pgadmin_user_emails.append(users[user]['email_address'])
    f.write("ALEX ADDING TEST foo@bar.com USER HERE FOR DEV\n")
    pgadmin_user_emails.append('foo@bar.com')
    query = ("DELETE FROM user where username = '{0}'"
             .format('foo@bar.com'))
    cursor.execute(query)
    connection.commit()
    # List of users already in pgadmin user records
    existing_users = {}
    query = "select * from user"
    for row in cursor.execute(query):
        existing_users[row[1]] = row[0]
    f.write(str(existing_users) + "\n")
    # List of system roles from pgadmin
    pgadmin_roles = {}
    query = "select id, name from role"
    for row in cursor.execute(query):
        pgadmin_roles[row[1]] = row[0]
    # Other configuration data
    postgresql_port = __salt__['pillar.get']('postgresql_port')
    connection_params = ("{\"sslmode\": \"require\", " +
                         "\"passfile\": \"/pgpass\", " +
                         "\"connect_timeout\": 10}")
    local_ips = __salt__['grains.get']('ipv4')
    postgres_server_ip = None
    for ip in local_ips:
        if __salt__['pillar.get']('ip_network') in ip:
            postgres_server_ip = ip
            break

    # 2.
    # Admin user

    admin_password = (''.join(random.choice(string.ascii_letters +
                                            string.digits)
                              for x in range(30)))  # pyright: ignore
    f.write("ADMINPASSWORD: " + str(admin_password) + " \n")
    if admin_user_email not in existing_users:
        # 2b1.
        f.write("Adding " + str(admin_user_email) + " admin user entry\n")
    # 2a1a.
    query = ("INSERT INTO roles_users (user_id, role_id) VALUES ({0}, {1})"
             .format(existing_users[admin_user_email],
                     pgadmin_roles['Administrator']))
    cursor.execute(query)
    query = ("INSERT INTO servergroup (user_id, name) VALUES ({0}, '{1}')"
             .format(existing_users[admin_user_email],
                     frontend_server_groupname))
    cursor.execute(query)
    connection.commit()
    query = ("select id from servergroup where user_id = {0} and name = '{1}'"
             .format(existing_users[admin_user_email],
                     frontend_server_groupname))
    cursor.execute(query)
    servergroup_id = cursor.fetchone()[0]
    for frontend_database in frontend_databases:
        comment = frontend_databases[frontend_database]['pgadmin_comment']
        name = frontend_databases[frontend_database]['pgadmin_name']
        query = ("INSERT INTO server (" +
                 "user_id, " +
                 "servergroup_id, " +
                 "name, " +
                 "host, " +
                 "port, " +
                 "maintenance_db, " +
                 "username, " +
                 "comment, " +
                 "db_res, " +
                 "shared, " +
                 "connection_params " +
                 ") VALUES (" +
                 "{0}, {1}, '{2}', '{3}', {4}, '{5}', "
                 .format(existing_users[admin_user_email],
                         servergroup_id,
                         name,
                         postgres_server_ip,
                         postgresql_port,
                         frontend_databases[frontend_database]['name']) +
                 "'{0}', '{1}', '{2}', {3}, '{4}')"
                 .format(frontend_databases[frontend_database]['user'],
                         comment,
                         frontend_databases[frontend_database]['name'],
                         1,
                         connection_params))
        cursor.execute(query)
    connection.commit()

    # Admin password
    if admin_user_email in existing_users:
        # 2a1b.
        if not set_pgadmin_password(admin_user_email, admin_password):
            return False
    # 2a1c.
    pf = open(pgadmin_password_file, "w")
    pf.write(admin_password)
    pf.close()
    os.chmod(pgadmin_password_file, 0o600)
    uid = pwd.getpwnam(pgadmin_default_user).pw_uid
    gid = grp.getgrnam(pgadmin_default_user).gr_gid
    os.chown(pgadmin_password_file, uid, gid)

    # Non-admin users

    osid = 1
    for pgadmin_user in pgadmin_user_emails:
        if pgadmin_user not in existing_users:
            # 2b1.
            f.write("Adding " + pgadmin_user + " user entry\n\n")
            user_password = (''.join(random.choice(string.ascii_letters +
                                                   string.digits)
                                     for x in range(30)))  # pyright: ignore
            masterpass_check = \
                (''.join(random.choice(string.ascii_letters + string.digits)
                         for x in range(106)))  # pyright: ignore
            fs_uniquifier = (''.join(random.choice(string.ascii_letters +
                                                   string.digits)
                                     for x in range(32)))  # pyright: ignore
            query = ("INSERT INTO user (" +
                     "email, " +
                     "password, " +
                     "active, " +
                     "masterpass_check, " +
                     "username, " +
                     "auth_source, " +
                     "fs_uniquifier " +
                     ") VALUES (" +
                     "'{0}', '{1}', {2}, '{3}', '{4}', '{5}', '{6}')"
                     .format(pgadmin_user,
                             None,
                             1,
                             masterpass_check,
                             pgadmin_user,
                             'internal',
                             fs_uniquifier))
            f.write("QUERY " + query + "\n\n")
            cursor.execute(query)
            connection.commit()
            f.write("HERE1\n\n")
            f.write("HERE1" + str(pgadmin_user) + "\n\n")
            f.write("HERE1" + str(user_password) + "\n\n")
            if not set_pgadmin_password(pgadmin_user, user_password):
                return False
            f.write("HERE2\n\n")
            query = ("select * from user where username = '{0}'"
                     .format(pgadmin_user))
            f.write("HERE3\n\n")
            cursor.execute(query)
            f.write("HERE4\n\n")
            row = cursor.fetchone()[0]
            f.write("HERE5\n\n")
            existing_users[row[1]] = row[0]
            f.write("HERE6\n\n")
            foo()
        # 2a2a.
        f.write("Adding " + pgadmin_user + " data\n\n")
        query = ("INSERT INTO roles_users (user_id, role_id) VALUES ({0}, {1})"
                 .format(existing_users[pgadmin_user],
                         pgadmin_roles['User']))
        cursor.execute(query)
        for frontend_database in frontend_databases:
            name = frontend_databases[frontend_database]['pgadmin_name']
            query = ("INSERT INTO sharedserver (" +
                     "user_id, " +
                     "server_owner, " +
                     "servergroup_id, " +
                     "name, " +
                     "host, " +
                     "port, " +
                     "maintenance_db, " +
                     "username, " +
                     "shared, " +
                     "osid, " +
                     "connection_params " +
                     ") VALUES (" +
                     "{0}, '{1}', {2}, '{3}', '{4}', {5}, "
                     .format(existing_users[pgadmin_user],
                             admin_user_email,
                             servergroup_id,
                             name,
                             postgres_server_ip,
                             postgresql_port) +
                     "'{0}', '{1}', {2}, {3}, '{4}')"
                     .format(frontend_databases[frontend_database]['name'],
                             frontend_databases[frontend_database]['user'],
                             1,
                             osid,
                             connection_params))
            cursor.execute(query)
            osid = osid + 1
        connection.commit()
    f.close()
    return True
