#!/bin/bash

expired_list="$(apt-key list | grep expired)"
while read -r line
do
  IFS=' '
  read -ra expired_key <<< "$line"
  IFS=/
  read -ra key_id <<< "${expired_key[1]}"
  if [ ! -z "$key_id" ]
  then
    echo "Updating ${key_id[1]}"
    apt-key adv --keyserver keys.gnupg.net --recv-keys "${key_id[1]}"
  fi
done <<< "$expired_list"
exit 0
