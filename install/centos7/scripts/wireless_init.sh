#!/bin/sh

DRIVER='os/linux/mt7601Usta.ko'
DRIVER_SRC='wireless/mt7601usta/src/'
NETWORK_FILE_SRC='wireless/ifcfg-ra0'
NETWORK_FILE_TGT='/etc/sysconfig/network-scripts/ifcfg-ra0'
PING_CHECK_IP='8.8.8.8'
TMP_INSTALL='/tmp/olympus/'
WPA_CONF_SRC='wireless/wpa_supplicant/wpa_supplicant.conf'
WPA_CONF_TGT='/etc/wpa_supplicant/wpa_supplicant.conf'
WPA_INIT_SRC='wireless/wpa_supplicant/wirelessusb'
WPA_INIT_TGT='/etc/rc.d/init.d/wirelessusb'
WPA_SYS_SRC='wireless/wpa_supplicant/wpa_supplicant'
WPA_SYS_TGT='/etc/sysconfig/wpa_supplicant'

echo 'CentOS wireless installation utility for Olympus'
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
cp -rp ../src/wireless $TMP_INSTALL

echo 'Building and installing USB wifi driver...'
cd $TMP_INSTALL$DRIVER_SRC
make -w
if [ "$?" != '0' ]
then
    echo 'Error during make while installing USB wifi driver; terminating...'
    exit 1
fi
insmod $TMP_INSTALL$DRIVER_SRC$DRIVER
make install
if [ "$?" != '0' ]
then
    echo 'Error installing USB wifi driver; terminating...'
    exit 1
fi
cp -p $TMP_INSTALL$NETWORK_FILE_SRC $NETWORK_FILE_TGT
chown root:root $NETWORK_FILE_TGT
chmod 0644 $NETWORK_FILE_TGT

echo 'Installing wpa_supplicant configuration...'
cp -p $TMP_INSTALL$WPA_CONF_SRC $WPA_CONF_TGT
chown root:root $WPA_CONF_TGT
chmod 0600 $WPA_CONF_TGT
sed -i -e 's/\$SSID/'"$ssid"'/' $WPA_CONF_TGT
sed -i -e 's/\$PSK/'"$password"'/' $WPA_CONF_TGT
cp -p $TMP_INSTALL$WPA_SYS_SRC $WPA_SYS_TGT
chown root:root $WPA_SYS_TGT
chmod 0644 $WPA_SYS_TGT
cp -p $TMP_INSTALL$WPA_INIT_SRC $WPA_INIT_TGT
chown root:root $WPA_INIT_TGT
chmod 0755 $WPA_INIT_TGT
rm -f /etc/rc.d/rc3.d/S09wirelessusb
ln -s $WPA_INIT_TGT /etc/rc.d/rc3.d/S09wirelessusb
rm -f /etc/rc.d/rc5.d/S09wirelessusb
ln -s $WPA_INIT_TGT /etc/rc.d/rc5.d/S09wirelessusb

echo 'Enabling network services...'
chkconfig NetworkManager off
chkconfig messagebus on
if [ "$?" != '0' ]
then
    echo 'Error enabling messagebus; terminating...'
    exit 1
fi
chkconfig wpa_supplicant on
if [ "$?" != '0' ]
then
    echo 'Error enabling wpa_supplicant; terminating...'
    exit 1
fi
chkconfig network on
if [ "$?" != '0' ]
then
    echo 'Error enabling network; terminating...'
    #exit 1
fi
service wpa_supplicant stop
service wpa_supplicant start
if [ "$?" != '0' ]
then
    echo 'Error restarting wpa_supplicant; terminating...'
    exit 1
fi
service network stop
service network start
if [ "$?" != '0' ]
then
    echo 'Error restarting network; terminating...'
    exit 1
fi
killall dhclient >/dev/null 2>&1
dhclient ra0
if [ "$?" != '0' ]
then
    echo 'Error opening wireless connection to ra0; terminating...'
    exit 1
fi
sleep 1

echo 'Testing network connectivity'
if ! ping -c 1 $PING_CHECK_IP &> /dev/null
then
    echo 'Error during ping check of wireless connection; terminating...'
    exit 1
fi

echo 'Cleanup'
rm -rf $TMP_INSTALL

echo 'SUCCESS'
