#!/bin/sh

sudo -u uwsgi /usr/bin/python3 /srv/www/django/manage.py runserver 1>>/var/log/devserver.log 2>>/var/log/devserver.log &
if [ $? -eq 0 ]
then
  pkill -f runserver
  if [ $? -eq 0 ]
  then
    echo "Dev server stopped"
	exit 0
  else
    echo "Failure when stopping dev server"
	exit 1
  fi
else
  echo "Dev server not running"
  exit 0
fi
