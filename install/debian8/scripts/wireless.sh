#!/bin/bash

DRIVER='mt7601Usta.ko'
NETWORK_FILE_SRC='src/wireless_init/interfaces'
NETWORK_FILE_TGT='/etc/network/interfaces'
TMP_INSTALL='/tmp/olympus'

WPA_CONF='wpa_supplicant.conf'
WPA_CONF_DIR='/etc/wpa_supplicant/'
WPA_CONF_SRC='src/wireless_init/wpa_supplicant.conf'

echo 'Debian wireless networking initialization utility for Olympus installation'
if [[ $EUID -ne 0 ]]
then
   echo "This script must be run as root" 1>&2
   exit 1
fi
echo -n 'Enter name (SSID) of wireless access point > '
read ssid
echo -n 'Enter password for wireless access point > '
read -s password
echo ''
echo 'When ready, click "Y" (yes) to proceed...'
read -s -n 1 proceed
if [ "$proceed" != 'Y' ] && [ "$proceed" != 'y' ]
then
    echo 'Terminated'
    exit 1
fi

echo 'Copying installation files...'
rm -rf $TMP_INSTALL
mkdir -p $TMP_INSTALL
cp -rp ../src $TMP_INSTALL

echo 'Creating local apt repository and updating aptitude database...'
mkdir -p /var/cache/apt-local/
cp -rp $TMP_INSTALL/src/archives /var/cache/apt-local/
cp $TMP_INSTALL/src/wireless_init/sources.list /etc/apt/sources.list
apt-get update

echo 'Installing USB wifi driver with dependencies...'
cd $TMP_INSTALL/src/archives
dpkg -i ./mt7601-sta-dkms_3.0.0.4-0-201602170733-rev26-pkg4-ubuntu16.04.1_all.deb
apt-get --yes --force-yes install -f
installed_driver=$(find /lib | grep $DRIVER)
insmod $installed_driver
if [ "$?" != '0' ]
then
    echo 'Error installing USB wifi driver; terminating...'
    exit 1
fi

echo 'Updating network configuration file for wireless'
echo $NETWORK_FILE_TGT
cp -p $TMP_INSTALL/$NETWORK_FILE_SRC $NETWORK_FILE_TGT
chown root:root $NETWORK_FILE_TGT
chmod 0644 $NETWORK_FILE_TGT

echo 'Installing wpa_supplicant configuration...'
echo $WPA_CONF_DIR$WPA_CONF
mkdir -p $WPA_CONF_DIR
cp -p $TMP_INSTALL/$WPA_CONF_SRC $WPA_CONF_DIR$WPA_CONF
chown root:root $WPA_CONF_DIR$WPA_CONF
chmod 0600 $WPA_CONF_DIR$WPA_CONF
sed -i -e 's/\$SSID/'"$ssid"'/' $WPA_CONF_DIR$WPA_CONF
sed -i -e 's/\$PSK/'"$password"'/' $WPA_CONF_DIR$WPA_CONF

echo 'Rebooting to enable wpa_supplicant connection...'
shutdown --reboot
