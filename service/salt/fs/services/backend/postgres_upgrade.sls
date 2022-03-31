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

#}
