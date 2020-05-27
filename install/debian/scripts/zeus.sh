#!/bin/bash

TITLE='Supervisor installation utility for Olympus'
cd "$(dirname "$0")"
source './init.sh'

cat << EOF
Available supervisor installation types:

1. Unified. Web service and back end combined on one server.
2. Stand alone. Back end server separate from web server.

EOF
printf "Choose type (1/2). > "
read installation_type
IFS=$'\n'
if [[ $installation_type -eq 1 ]]
then
    echo
    echo 'Unified supervisor.'
elif [[ $installation_type -eq 2 ]]
then
    echo
    echo 'Stand alone supervisor'
else
    echo 'ERROR: Bad choice; exiting.' 1>&2
    exit 1
fi

echo -n 'When ready, enter "Y" (yes) to proceed. > '
read proceed
if [ "$proceed" != 'Y' ] && [ "$proceed" != 'y' ]
then
    echo 'Terminated via user input.'
    exit 0
fi
echo

echo 'Checking network connectivity.'
if ! ping -c 1 $PING_TEST_IP &> /dev/null
then
    echo "ERROR: Network check failed, unable to ping [$PING_TEST_IP]. Run networking.sh? Exiting." 1>&2
    exit 1
fi

echo 'Adding apt sources.'
cp ${SOURCE_PATH_OS}release/$VERSION_CODENAME/sources.list /etc/apt/sources.list
if [ $? != 0 ]
then
    echo 'ERROR: Failed copying sources.list for current release; exiting.' 1>&2
    exit 1
fi

echo 'Retrieving and installing SaltStack GPG keys.'
wget --quiet -O - $SALT_GPG_KEY_URL | apt-key add - 
if [ $? != 0 ]
then
    echo 'ERROR: Failed to install Salt keys; exiting.' 1>&2
    exit 1
fi

echo 'Updating aptitude database.'
apt-get update >> /dev/null
if [ $? != 0 ]
then
    echo 'ERROR: Failure during update of aptitude database; exiting.' 1>&2
    exit 1
fi

echo 'Installing Salt master/minion.'
apt-get -y install salt-master >> /dev/null
if [ $? != 0 ]
then
    echo 'ERROR: Failure installing salt master; exiting.' 1>&2
    exit 1
fi
apt-get -y install salt-minion >> /dev/null
if [ $? != 0 ]
then
    echo 'ERROR: Failure installing salt minion; exiting.' 1>&2
    exit 1
fi

echo 'Initializing git user for git service.'
if id -u $GIT_OWNER > /dev/null 2>&1
then
    deluser $GIT_OWNER --remove-home --quiet
fi
useradd $GIT_OWNER --create-home
if [ $? != 0 ]
then
    echo 'ERROR: Unable to add git user; exiting.' 1>&2
    exit 1
fi

echo 'Initializing git set-up.'
rm -rf $GIT_PATH
runuser -l $GIT_OWNER -c "mkdir -p $GIT_PATH"
if [ $? != 0 ]
then
    echo 'ERROR: Failed to add git directory; exiting.' 1>&2
    exit 1
fi
runuser -l $GIT_OWNER -c "cd $GIT_PATH; git init --bare; git config core.sharedRepository true"
if [ $? != 0 ]
then
    echo 'ERROR: Unable to configure git repository; exiting.' 1>&2
    exit 1
fi
if [ ! -d ../../../BAK/repository/$GIT_REPO ]
then
    echo "ERROR: Git repository [../../../BAK/repository/$GIT_REPO] not found in installation source; exiting." 1>&2
    exit 1
fi
cp -rp ../../../BAK/repository/$GIT_REPO $GIT_PATH
if [ $? != 0 ]
then
    echo "ERROR: Unable to copy git repository to [$GIT_PATH]; exiting." 1>&2
    exit 1
fi
chmod -R g+ws $GIT_PATH/$GIT_REPO
chgrp -R $GIT_OWNER $GIT_PATH/$GIT_REPO

echo 'Updating salt configuration.'
cd /etc/salt/master.d
echo 'Extracting /etc/salt/master.d/core.conf.'
git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/fs/saltstack/files/master.d core.conf | tar -x
if [ $? != 0 ]
then
    echo 'ERROR: Failure during extraction of master core.conf; exiting.' 1>&2
    exit 1
fi
echo 'Extracting /etc/salt/master.d/reactor.conf.'
git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/fs/saltstack/files/master.d reactor.conf | tar -x
if [ $? != 0 ]
then
    echo 'ERROR: Failure during extraction of master reactor.conf; exiting.' 1>&2
    exit 1
fi
chown root:root *
chmod 0644 *
cd /etc/salt/minion.d
echo 'Extracting /etc/salt/minion.d/core.conf.'
git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/fs/saltstack/files/minion.d core.conf | tar -x
if [ $? != 0 ]
then
    echo 'ERROR: Failure during extraction of minion core.conf; exiting.' 1>&2
    exit 1
fi
if [[ $installation_type -eq 1 ]]
then
    echo 'Extracting unified minion configuration.'
    git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/fs/saltstack/files/minion.d unified.conf | tar -x
else
    echo 'Extracting stand alone minion configuration.'
    git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/fs/saltstack/files/minion.d supervisor.conf | tar -x
fi
if [ $? != 0 ]
then
    echo 'ERROR: Failure during extraction of minion server configuration; exiting.' 1>&2
    exit 1
fi
chown root:root *
chmod 0644 *

service salt-minion restart
service salt-master restart
sleep 5
salt-key -A -y >> /dev/null
if [ $? != 0 ]
then
    echo 'ERROR: Failure connecting minion zeus to zeus master; exiting.' 1>&2
    exit 1
fi

iterations=0
max_iterations=10
pattern='zeus:\s*True'
saltreply=''
sleep=10
while ! [[ "$saltreply" =~ $pattern ]]
do
    if [[ $iterations > 0 ]]
    then
        sleep $sleep
    fi
    iterations=$((iterations+1))
    if [[ $iterations > $max_iterations ]]
    then
        echo 'ERROR: Minion not responding; exiting per configuration.' 1>&2
        exit 1
    fi
    echo 'Waiting for minion to answer ping.'
    saltreply=`salt '*' test.ping`
    echo '['$saltreply']'
done

echo 'Checking network connectivity prior to highstate.'
if ! ping -c 1 $PING_TEST_IP &> /dev/null
then
    echo "ERROR: Network check failed, unable to ping [$PING_TEST_IP]; exiting." 1>&2
    exit 1
fi

echo 'Running salt highstate to overlay configuration.'
cd
salt '*' state.highstate pillar='{"pkg_latest": true}'
if [ $? != 0 ]
then
    echo 'ERROR: Failure while connecting minion zeus to zeus master; exiting.' 1>&2
    exit 1
fi

echo 'Success!'
echo 'Rebooting to finalize configuration.'
#shutdown --reboot now && exit 0
