#!/usr/bin/env python3

from subprocess import Popen

cmd_str = ('/usr/bin/python3 /srv/www/django/manage.py runserver 1' +
           '>>/var/log/devserver/devserver.log 2>>' +
           '/var/log/devserver/devserver.log &')
proc = Popen([cmd_str],
             shell=True,
             stdin=None,
             stdout=None,
             stderr=None,
             close_fds=True)
