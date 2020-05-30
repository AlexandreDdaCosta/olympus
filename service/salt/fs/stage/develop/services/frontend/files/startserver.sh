#!/bin/sh

sudo -u uwsgi /usr/bin/python3 /srv/www/django/manage.py runserver 1>>/var/log/devserver.log 2>>/var/log/devserver.log &
