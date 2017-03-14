#!/usr/bin/env python3

from subprocess import Popen
 
cmd_str = 'sudo -u uwsgi /usr/bin/python3 /srv/www/django/manage.py runserver 0.0.0.0:8000 1>>/var/log/devserver.log 2>>/var/log/devserver.log &'
proc = Popen([cmd_str], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
