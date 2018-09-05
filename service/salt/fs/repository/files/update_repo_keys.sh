#!/bin/sh

apt-key list | grep expired
if [ $? -eq 0 ]
then
  echo "OK"
  exit 1
else
  echo "Key verification failure"
  exit 1
fi
