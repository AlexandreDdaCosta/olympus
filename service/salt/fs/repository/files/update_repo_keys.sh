#!/bin/bash

expired_key=false
apt_key_list="$(apt-key list)"
while read -r line
do
  if [ "$expired_key" = true ]
  then
    IFS=' '
    read -ra hex_quartets <<< "$line"
    IFS=/
    echo "Updating ${hex_quartets[-2]}${hex_quartets[-1]}"
    apt-key adv --keyserver keys.gnupg.net --recv-keys "${hex_quartets[-2]}${hex_quartets[-1]}"
    expired_key=false
  else
    (echo "$line" | grep -Eq "expired:") && expired_key=true
  fi
done <<< "$apt_key_list"
exit 0
