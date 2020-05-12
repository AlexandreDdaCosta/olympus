#!/bin/bash

# Not yet tested. Bin file may be unnecessary. Be aware when trying for first time.

TMP_INSTALL='/tmp/olympus'

BIN_FILE_SRC='src/networking_init/mt7601u.bin'
BIN_FILE_TGT='/lib/firmware/mt7601u.bin'
NETWORK_FILE_SRC='src/networking_init/interfaces'
NETWORK_FILE_TGT='/etc/network/interfaces'
WPA_CONF='wpa_supplicant.conf'
WPA_CONF_DIR='/etc/wpa_supplicant/'
WPA_CONF_SRC='src/networking_init/wpa_supplicant.conf'

echo 'Debian networking initialization utility for Olympus installation'
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

echo 'Installing USB wifi driver with dependencies...'
cd $TMP_INSTALL/src/archive
dpkg -i ./firmware-misc-nonfree_20161130-3_all.deb
dpkg -i ./firmware-bnx2_20161130-3_all.deb
modprobe mt7601u
if [ "$?" != '0' ]
then
    echo 'Error installing USB wifi driver; terminating...'
    exit 1
fi

echo 'Adding mt7601u.bin...'
cp -p $TMP_INSTALL/$BIN_FILE_SRC $BIN_FILE_TGT
chown root:root $BIN_FILE_TGT
chmod 0644 $BIN_FILE_TGT

echo 'Updating network configuration file...'
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
