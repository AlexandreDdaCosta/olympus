#!/usr/bin/env python3

"""
A simple and crude utility script that connects to the local SQLite
database used by pgadmin and retrieves basic information about the tables
used to store user data and the current contents of those tables.
"""

import sqlite3

connection = sqlite3.connect("/var/lib/pgadmin/pgadmin4.db")
cursor = connection.cursor()
print("tables\n")
for row in cursor.execute("select * from sqlite_master where type='table'"):
    print(row)
tables = ('user',
          'servergroup',
          'server',
          'sharedserver',
          'role',
          'roles_users')
for name in tables:
    print("\n{}\n".format(name))
    query = "select sql from sqlite_schema where name = '{}'".format(name)
    for row in cursor.execute(query):
        formatted_output = str(row).replace('\\n', '\n').replace('\\t', '\t')
        print(formatted_output)
    query = "select * from {}".format(name)
    for row in cursor.execute(query):
        print(row)
