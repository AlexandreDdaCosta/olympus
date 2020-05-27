#!/bin/bash

/usr/bin/clear

if [[ $EUID -ne 0 ]]
then
    echo 'ERROR: This script must be run as root; exiting.' 1>&2
    exit 1
fi

CONF_FILE_INSTALL="../../etc/install.conf"
if [ ! -f $CONF_FILE_INSTALL ]
then
    echo "ERROR: Installation configuration file [$CONF_FILE_INSTALL] not found in root install /etc directory; exiting." 1>&2
    exit 1
fi
source $CONF_FILE_INSTALL
if [ ! -f $CONF_FILE_OS ]
then
    echo "ERROR: Debian configuration file [$CONF_FILE_OS] not found; exiting." 1>&2
    exit 1
fi
source $CONF_FILE_OS
if [ -z ${OS_RELEASE_FILE+x} ]
then 
    echo "ERROR: Variable [OS_RELEASE_FILE] not set in OS configuration [$CONF_FILE_OS]; exiting." 1>&2
    exit 1
fi
if [ ! -f $OS_RELEASE_FILE ]
then
    echo "ERROR: Debian release file [$OS_RELEASE_FILE] not found; exiting." 1>&2
    exit 1
fi
source $OS_RELEASE_FILE
if [ -z ${OS_NAME+x} ]
then 
    echo "ERROR: Variable [OS_NAME] not set in OS configuration [$CONF_FILE_OS]; exiting." 1>&2
    exit 1
fi
if [[ $NAME != $OS_NAME ]]
then
    echo "ERROR: Configuration's OS name [$OS_NAME] does not match release file [$OS_RELEASE_FILE]; exiting." 1>&2
    exit 1
fi
if [ ! -z ${MAX_OS_VERSION+x} ] && [[ $VERSION_ID -gt $MAX_OS_VERSION ]]
then
    echo "ERROR: OS version [$VERSION_ID] is over the maximum [$MAX_OS_VERSION] supported per OS configuration file; exiting." 1>&2
    exit 1
fi
if [ ! -z ${MIN_OS_VERSION+x} ] && [[ $VERSION_ID -lt $MIN_OS_VERSION ]]
then
    echo "ERROR: OS version [$VERSION_ID] is under the minimum [$MIN_OS_VERSION] supported per OS configuration file; exiting." 1>&2
    exit 1
fi

RELEASE_FILE_OS="${RELEASE_PATH_OS}${VERSION_CODENAME}.conf"
if [ -f $RELEASE_FILE_OS ]
then
    source $RELEASE_FILE_OS
fi

number_of_hyphens=${#TITLE}
hyphens=''
counter=0
while [ $counter -lt $number_of_hyphens ]
do
    counter=$(( $counter + 1 ))
    hyphens+='-'
done
cat << EOF
$hyphens
$TITLE
$hyphens

OS: $NAME
Release: $VERSION_ID
Code Name: $VERSION_CODENAME
 
EOF

