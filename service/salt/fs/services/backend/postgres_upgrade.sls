{#

Currently this shell encapsulates the steps used to upgrade postgres manually. This can potentially
be turned into an automated process.

There is also added commentary on manual steps useful in obtaining information needed for the upgrade.

Video tutorial: https://www.youtube.com/watch?v=15Pwl30Dut0

Unless noted, run steps as a privileged user under "sudo -i".

Informational
-------------

$ date
Thu 31 Mar 2022 12:33:32 PM EDT
$ sudo su - postgres
$ psql -c "select version();" 
...
PostgreSQL 9.6.24 on x86_64-pc-linux-gnu (Debian 9.6.24-1.pgdg100+1), compiled by gcc (Debian 8.3.0-6) 8.3.0, 64-bit
$ psql -c "show data_directory;"
...
/var/lib/postgresql/9.6/main
$ psql
postgres=# \l
...
                                  List of databases
   Name    |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
-----------+----------+----------+-------------+-------------+-----------------------
 app_data  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =Tc/postgres         +
           |          |          |             |             | postgres=CTc/postgres+
           |          |          |             |             | uwsgi=CTc/postgres
 olympus   | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
 postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
 template0 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
           |          |          |             |             | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
           |          |          |             |             | postgres=CTc/postgres
 user_data | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =Tc/postgres         +
           |          |          |             |             | postgres=CTc/postgres+
           |          |          |             |             | uwsgi=CTc/postgres
(6 rows)
postgres=# \q
$ exit

- Go to https://www.postgresql.org/download/linux/.  Select the proper distro button for added installation details.
- Verify psycopg compatibility with postgreSQL and Django:

https://www.psycopg.org/docs/news.html

As of "date", the following are compatible on Debian:
psycopg2 2.9.4
postgresql-14 (https://www.psycopg.org/docs/news.html#what-s-new-in-psycopg-2-9-2)
django 3.2.12 (4.0.3 is latest, but requires python >= 3.8. Current is 3.7.3; see
https://docs.djangoproject.com/en/4.0/faq/install/#faq-python-version-support)

* ---------- *

$ sudo apt install postgresql-14 
# New service starts autmatically, port 5433 per new conf file

$ sudo systemctl --type=service --state=running | grep postgres 
# Verifies running postgres services; at this stage, 9.6 and 14

$ sudo service postgresql stop 
# Stops both services

$ sudo su - postgres
$ /usr/lib/postgresql/14/bin/pg_upgrade -b /usr/lib/postgresql/9.6/bin -B /usr/lib/postgresql/14/bin -d /var/lib/postgresql/9.6/main -D /var/lib/postgresql/14/main -o '-c config_file=/etc/postgresql/9.6/main/postgresql.conf' -O '-c config_file=/etc/postgresql/14/main/postgresql.conf' -c
# Check cluster compatibility. Note added "-o" and "-O" options required for config file in /etc; expected location 
# /var/lib/postgresql/(9.6|14)/main. Also note format with -o/-O switch.
# Successful output:
# Performing Consistency Checks
# ...
# *Clusters are compatible*

$ /usr/lib/postgresql/14/bin/pg_upgrade -b /usr/lib/postgresql/9.6/bin -B /usr/lib/postgresql/14/bin -d /var/lib/postgresql/9.6/main -D /var/lib/postgresql/14/main -o '-c config_file=/etc/postgresql/9.6/main/postgresql.conf' -O '-c config_file=/etc/postgresql/14/main/postgresql.conf'
# Run actual upgrade: same as previous command without the "check" (-c) flag.
# Successful output:
# Performing Consistency Checks
# ...
# Upgrade Complete
# ...

$ psql -p 5433
postgres=# \l
# Visually verify transfer of old data.
postgres=# \q
$ exit
# End postgres user session
# Another option is to TEMPORARILY edit the Django local settings file to connect to upgrade port, then
# restart the relevant service and following up with an operational check:
# Open /srv/www/django/interface/settings_local.py
# Edit two occurrences of "'PORT': '5432'" to "'PORT': '5433'"
# service restart uwsgi

$ sudo cp -rp /var/lib/postgresql/9.6 /var/lib/postgresql/9.6.SAVED
# Backup old data files

* ---------- *

# Update salt files
# ./service/salt/pillar/services/backend.sls
#   In "backend-packages:":
#     "postgres-<old_version>" to "postgres-<new_version>"
#     "version:": old version to new version
# ./service/salt/fs/services/backend.sls
#   Update all references in following stanzas from old version to new version:
#     /etc/postgresql/<old_version>/main/pg_hba.conf:
#     /etc/postgresql/<old_version>/main/postgresql.conf:
#     postgresql:
#   Update salt://services/backend/files/pg_hba.conf using old parameters and latest version as model
#   Update salt://services/backend/files/postgresql.conf using old parameters and latest version as model

* ---------- *

sudo -i salt '*' state.highstate -v
# Adjust "server" of command depending on set-up

#}
