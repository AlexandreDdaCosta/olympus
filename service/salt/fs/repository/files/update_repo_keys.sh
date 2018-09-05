#!/bin/sh

pgrep -f runserver
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
