#!/bin/bash

# Clear out REST api tokens from redis
# Necessary when REST api passwords get regenerated

# Without this script, REST access will be denied until the old
# tokens expire.

if [ "$REDIS_DEFAULT_PASSWORD" != '' ]
then
    declare -a tokenarray
    readarray -t tokenarray < <(echo -e "auth default $REDIS_DEFAULT_PASSWORD\nKEYS '*:restapi:token'" | /usr/bin/redis-cli)
    for i in ${!tokenarray[@]}
    do
	if [[ ${tokenarray[i]}  =~ ^.*:restapi:token$ ]]
	then
            echo -e "auth default $REDIS_DEFAULT_PASSWORD\nDEL ${tokenarray[i]}" | /usr/bin/redis-cli
        fi
    done
    declare -a autharray
    readarray -t autharray < <(echo -e "auth default $REDIS_DEFAULT_PASSWORD\nKEYS 'restapi:auth:*'" | /usr/bin/redis-cli)
    for i in ${!autharray[@]}
    do
	if [[ ${autharray[i]}  =~ ^restapi:auth:.*$ ]]
	then
            echo -e "auth default $REDIS_DEFAULT_PASSWORD\nDEL ${autharray[i]}" | /usr/bin/redis-cli
        fi
    done
else
    /usr/bin/redis-cli KEYS "*:restapi:token" | xargs /usr/bin/redis-cli DEL
    /usr/bin/redis-cli KEYS "restapi:auth:*" | xargs /usr/bin/redis-cli DEL
fi
