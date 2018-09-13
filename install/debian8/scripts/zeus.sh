#!/bin/bash

GIT_OWNER='git'
GIT_PATH='/home/git/repository'
GIT_REPO='olympus.git'
PING_CHECK_IP='8.8.8.8'
TMP_INSTALL='/tmp/olympus'

echo 'Debian Olympus installation utility'
if [[ $EUID -ne 0 ]]
then
   echo "This script must be run as root" 1>&2
   exit 1
fi

installation_type='0'
while [ "$installation_type" != 'U' ] && [ "$installation_type" != 'u' ] && [ "$installation_type" != 'S' ] && [ "$installation_type" != 's' ]
do
  echo 'Choose (u)nified or (s)tandalone supervisor installation (U/S)'
  read -s -n 1 installation_type
  if [ "$installation_type" != 'U' ] && [ "$installation_type" != 'u' ] && [ "$installation_type" != 'S' ] && [ "$installation_type" != 's' ]
  then
      echo 'Invalid choice'
  fi
done

echo 'When ready, click "Y" (yes) to proceed...'
read -s -n 1 proceed
if [ "$proceed" != 'Y' ] && [ "$proceed" != 'y' ]
then
    echo 'Terminated'
    exit 1
fi

echo 'Testing network connectivity'
if ! ping -c 1 $PING_CHECK_IP &> /dev/null
then
    echo 'Error during ping check of network connectivity; terminating...'
    exit 1
fi

echo 'Copying installation files...'
rm -rf $TMP_INSTALL
mkdir -p $TMP_INSTALL
cp -rp ../src $TMP_INSTALL

echo 'Updating/creating local apt repository...'
mkdir -p /var/cache/apt-local/
cp -rp $TMP_INSTALL/src/archives /var/cache/apt-local/
cp $TMP_INSTALL/src/sources.list /etc/apt/sources.list

echo 'Installing Saltstack...'
echo 'Retrieving and installing Salt keys'
wget -O - https://repo.saltstack.com/apt/debian/8/amd64/latest/SALTSTACK-GPG-KEY.pub | apt-key add -
if [ "$?" != '0' ]
then
    echo 'Error installing Salt keys; terminating...'
    exit 1
fi
echo 'Updating aptitude database'
apt-get update
if [ "$?" != '0' ]
then
    echo 'Error updating aptitude database; terminating...'
    exit 1
fi

echo 'Installing Salt master/minion...'
apt-get -y install salt-master
if [ "$?" != '0' ]
then
    echo 'Error installing salt master; terminating...'
    exit 1
fi
apt-get -y install salt-minion
if [ "$?" != '0' ]
then
    echo 'Error installing salt minion; terminating...'
    exit 1
fi

echo 'Initializing git user for git service...'
if id -u $GIT_OWNER > /dev/null 2>&1; then
  deluser $GIT_OWNER
fi
useradd $GIT_OWNER --create-home
if [ "$?" != '0' ]
then
    echo 'Error adding git user; terminating...'
    exit 1
fi

echo 'Initializing git set-up...'
rm -rf $GIT_PATH
runuser -l $GIT_OWNER -c "mkdir -p $GIT_PATH"
if [ "$?" != '0' ]
then
    echo 'Error adding git directory; terminating...'
    exit 1
fi
runuser -l $GIT_OWNER -c "cd $GIT_PATH; git init --bare; git config core.sharedRepository true"
if [ "$?" != '0' ]
then
    echo 'Error configuring git repository; terminating...'
    exit 1
fi
cp -rp ../../misc/git/$GIT_REPO $GIT_PATH
if [ "$?" != '0' ]
then
    echo 'Error copying git repository; terminating...'
    exit 1
fi
chmod -R g+ws $GIT_PATH/$GIT_REPO
chgrp -R $GIT_OWNER $GIT_PATH/$GIT_REPO

echo 'Updating salt configuration...'
mkdir -p /etc/salt/shared_credentials
chmod 0700 /etc/salt/shared_credentials
cd /etc/salt/master.d
echo 'Extracting /etc/salt/master.d/core.conf from git'
git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/conf/master.d core.conf | tar -x
if [ "$?" != '0' ]
then
    echo 'Error extracting core.conf; terminating...'
    exit 1
fi
echo 'Extracting /etc/salt/master.d/reactor.conf from git'
git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/conf/master.d reactor.conf | tar -x
if [ "$?" != '0' ]
then
    echo 'Error extracting core.conf; terminating...'
    exit 1
fi
cd /etc/salt/minion.d
echo 'Extracting /etc/salt/minion.d/core.conf from git'
git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/conf/minion.d core.conf | tar -x
if [ "$?" != '0' ]
then
    echo 'Error extracting core.conf; terminating...'
    exit 1
fi
if [ "$installation_type" = 'U' ] || [ "$installation_type" = 'u' ]
then
    echo 'Unified server installation configuration...'
    git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/conf/minion.d unified.conf | tar -x
else
    echo 'Standalone server installation configuration...'
    git archive --remote=file://$GIT_PATH/$GIT_REPO HEAD:service/salt/conf/minion.d supervisor.conf | tar -x
fi

service salt-minion restart
service salt-master restart
sleep 5
salt-key -A -y
if [ "$?" != '0' ]
then
    echo 'Error connecting minion zeus to zeus master; terminating...'
    exit 1
fi

iterations=0
max_iterations=10
pattern='zeus:\s*True'
saltreply=''
sleep=10
while ! [[ "$saltreply" =~ $pattern ]]
do
  if (( $iterations > 0 ))
  then
    sleep $sleep
  fi
  iterations=$((iterations+1))
  if (( $iterations > $max_iterations ))
  then
    echo 'Minion not responding; exiting per configuration...'
    exit 1
  fi
  echo 'Waiting for minion to answer ping'
  saltreply=`salt '*' test.ping`
  echo '['$saltreply']'
done

echo 'Pausing, restart network'
service networking restart
sleep 10

echo 'Testing network connectivity pre highstate'
if ! ping -c 1 $PING_CHECK_IP &> /dev/null
then
    echo 'Error during pre-highstate ping check of network connectivity; terminating...'
    exit 1
fi

echo 'Running salt highstate to overlay configuration...'
cd
salt '*' state.highstate pillar='{"pkg_latest": true}'
if [ "$?" != '0' ]
then
    echo 'Error connecting minion zeus to zeus master; terminating...'
    exit 1
fi

echo 'Rebooting to finalize configuration...'
shutdown --reboot
