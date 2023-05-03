#!/bin/bash

if [ "$REDIS_DEFAULT_PASSWORD" != '' ]
then
    echo -e "auth default $REDIS_DEFAULT_PASSWORD\nflushall" | /usr/bin/redis-cli
    echo -e "auth default $REDIS_DEFAULT_PASSWORD\nflushall" | /usr/bin/redis-cli
else
    /usr/bin/redis-cli KEYS "restapi:auth*" | xargs /usr/bin/redis-cli DEL
    /usr/bin/redis-cli KEYS "*restapi:token" | xargs /usr/bin/redis-cli DEL
fi
