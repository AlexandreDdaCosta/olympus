#!/bin/bash

if [ -f /etc/redis/users.acl ]
then 
    default_password=grep default /etc/redis/users.acl | sed -e 's/.*>//'
    if [ "$default_password" == '' ]
    then
        /usr/bin/redis-cli acl load
    else
        echo -e "auth default $default_password\nacl load" | /usr/bin/redis-cli
    fi
else
    /usr/bin/redis-cli acl load
fi
