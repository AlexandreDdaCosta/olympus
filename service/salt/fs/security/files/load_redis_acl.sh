#!/bin/bash

# Load access control lists for redis

if [ "$REDIS_DEFAULT_PASSWORD" != '' ]
then
    echo -e "auth default $REDIS_DEFAULT_PASSWORD\nacl load" | /usr/bin/redis-cli
else
    /usr/bin/redis-cli acl load
fi
