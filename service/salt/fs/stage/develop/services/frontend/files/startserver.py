#!/usr/bin/env python3

from subprocess import Popen
 
cmd_str = 'sudo -u uwsgi /usr/bin/python3 /srv/www/django/manage.py runserver 1>>/var/log/devserver.log 2>>/var/log/devserver.log &'
proc = Popen([cmd_str], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

/usr/local/bin/startserver.py:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/startserver.py
    - user: root
    - require:
      - sls: services/frontend

devserver-start:
  cmd.run:
    - name: /usr/local/bin/startserver.py

