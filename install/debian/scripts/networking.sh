#!/bin/bash

TITLE='Networking configuration utility for Olympus installation'
cd "$(dirname "$0")"
source './init.sh'

cat << EOF

Note: When a restart is reboot is required to enable an interface, options are limited to
the configured start-up network configuration.

Available network interfaces:

1. PCI Ethernet
2. USB Wifi

EOF
printf "Choose interface (1/2). > "
read interface_type
IFS=$'\n'
if [[ $interface_type -eq 1 ]]
then
    echo
    echo 'Ethernet network, onboard controller.'
    adapter_conf_path="${CONF_PATH_ADAPTERS}ethernet/pci/"
    hardware=(`/usr/bin/lspci | /usr/bin/grep 'Ethernet controller'`)
elif [[ $interface_type -eq 2 ]]
then
    echo
    echo 'Wifi network, USB adapter.'
    WIFI_SSID=''
    adapter_conf_path="${CONF_PATH_ADAPTERS}wireless/usb/" hardware=(`/usr/bin/lsusb`)
    while [[ $WIFI_SSID == '' ]]
    do
        echo -n 'Enter name (SSID) of wireless access point. > '
        read WIFI_SSID
    done
    WIFI_PASSWORD=''
    while [[ $WIFI_PASSWORD == '' ]]
    do
        echo -n 'Enter password for wireless access point. > '
        read -s WIFI_PASSWORD
        echo
    done
    echo -n 'Echo back password to confirm? Enter "Y" (yes) if so. > '
    read echo_back
    if [ "$echo_back" == 'Y' ] || [ "$echo_back" == 'y' ]
    then
        echo "Password: [$WIFI_PASSWORD]"
    fi
    echo
else
    echo 'ERROR: Bad choice; exiting.' 1>&2
    exit 1
fi
if [ "${#hardware[@]}" == '0' ]
then
    echo "ERROR: Unable to find specified type of attached hardware; hardware may need to be attached. Exiting." 1>&2
    exit 0
else
    echo 'Located compatible hardware specification.'
fi
adapters=(`ls ${adapter_conf_path}`)
unset IFS

ADAPTER=''
HARDWARE=''
for hardware_item in "${hardware[@]}"
do
    for adapter_name in "${adapters[@]}"
    do
        if [[ $hardware_item == *"$adapter_name"* ]]
        then
            ADAPTER=$adapter_name
            HARDWARE=$hardware_item
            break
        fi
    done
    if [[ $ADAPTER != '' ]]
    then
        break
    fi
done
# Initialized variables from $adapter_conf_file
HARDWARE_MODEL=''
HARDWARE_NAME=''
NETWORK_INTERFACE=''
if [[ $ADAPTER == '' ]]
then
    echo "ERROR: No matching adapters found for attached hardware; hardware may need attachment/installing; exiting." 1>&2
    exit 0
else
    adapter_conf_file="${adapter_conf_path}$ADAPTER/adapter.conf"
    if [ ! -f "${adapter_conf_file}" ]
    then
        echo "ERROR: Debian release file [$OS_RELEASE_FILE] not found; exiting." 1>&2
        exit 1
    fi
    source "$adapter_conf_file"
    echo "Located compatible adapter [$ADAPTER] for hardware [$HARDWARE_NAME]"
fi

cat << EOF

Select server type for IP setting or enter your own IP:

1. Unified or web server
2. Supervisor server
3. All other server types
4. Specify IP

EOF
printf 'Choose (1/2/3/4). > ' 
read server_type
IP=''
if [[ $server_type -eq 1 ]]
then
    IP=$LAN_IP_CORE
    echo
    echo "Unified/web server ($IP)."
elif [[ $server_type -eq 2 ]]
then
    IP=$LAN_IP_SUPERVISOR
    echo
    echo "Supervisor server ($IP)."
elif [[ $server_type -eq 3 ]]
then
    echo
    echo 'Other server type (dynamic IP).'
elif [[ $server_type -eq 4 ]]
then
    printf 'Enter IP (Q/q to quit). > '
    while [[ $IP == '' ]]
    do
        read IP
        if [[ $IP == 'Q' ]] || [[ $IP == 'q' ]]
        then
            echo 'Aborted by user; exiting.'
            exit 0
        elif [[ ! $IP =~ $IP_REGEX ]]
        then
            printf 'Invalid IP, reenter (Q/q to quit): '
            IP=''
        fi
    done
    echo
    echo "Custom IP ($IP)."
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

adapter_dependencies_file="${adapter_conf_path}$ADAPTER/release/$VERSION_CODENAME/dependencies"
if [ -f $adapter_dependencies_file ]
then
    echo 'Verifying and installing dependencies.'
    adapter_dependencies_directory="${SOURCE_PATH_OS}release/$VERSION_CODENAME/archives/"
    IFS=$'\n'
    dependencies=(`cat $adapter_dependencies_file`)
    IFS=' '
    for dependency in "${dependencies[@]}"
    do
        read -r -a package <<< "$dependency"
        installed_package_check=`/usr/bin/apt list --installed ${package[0]} 2>/dev/null | grep ${package[0]}`
        installed_package=(${installed_package_check})
        installed_version=${installed_package[1]}
        source_file="$adapter_dependencies_directory${package[1]}"
        if [[ ! -f $source_file ]]
        then
            echo "ERROR: Debian package [$source_file] not found in installation source; exiting." 1>&2
            exit 1
        fi
        source_package_check=`/usr/bin/dpkg-deb --info $source_file | grep Version`
        source_package=(${source_package_check})
        source_version=${source_package[1]}
        unset IFS
        install=false
        if [[ -n $installed_version ]]
        then
            version_check=`/usr/bin/dpkg --compare-versions $installed_version lt $source_version && echo true`
            if [ "$version_check" = true ]
            then
                install=true
                echo "Old version of package [${package[0]}] installed; updating."
            else
                version_check=`/usr/bin/dpkg --compare-versions $source_version lt $installed_version && echo true`
                if [ "$version_check" = true ]
                then
                    echo "Newer version of package [${package[0]}] already installed; skipping."
                else
                    echo "Package [${package[0]}] installed and up-to-date; skipping."
                fi
            fi
        else
            install=true
        fi
        if [ "$install" = true ]
        then
            echo "Installing ${package[0]}."
            /usr/bin/dpkg -i $source_file 1>/dev/null
        fi
    done
    unset IFS
else
    echo 'No dependencies specified.'
fi

adapter_modules_directory="${adapter_conf_path}$ADAPTER/modules/"
if [ -d $adapter_modules_directory ]
then
    modules=(`ls $adapter_modules_directory`)
    if [ "${#modules[@]}" != '0' ]
    then
        echo 'Installing and verifying modules.'
        for module in "${modules[@]}"
        do
            IFS=.
            module_name=($module)
            unset IFS
            echo "Installing ${module_name[0]}."
            path_to_module="$adapter_modules_directory$module"
            UNAME=`/usr/bin/uname -r`
            if [[ $interface_type -eq 1 ]]
            then
                module_installation_path="/lib/modules/$UNAME/kernel/drivers/net/ethernet/"
            else
                # [[ $interface_type -eq 2 ]]
                module_installation_path="/lib/modules/$UNAME/kernel/drivers/net/wireless/"
            fi
            module_check=(`/usr/sbin/modinfo ${module_name[0]} | grep filename`)
            target_file="$module_installation_path$module"
            if [[ "${module_check[1]}" != "$target_file" ]]
            then
                /usr/bin/install -p -m 644 $path_to_module $module_installation_path
                /sbin/depmod -a $UNAME
                sleep 1
                module_check=(`/usr/sbin/modinfo ${module_name[0]} | grep filename`)
                target_file="$module_installation_path$module"
                if [[ "${module_check[1]}" != "$target_file" ]]
                then
                    echo "ERROR: Failed to verify installation of module [${module_name[0]}] using modinfo; exiting." 1>&2
                fi
            fi
        done
    fi
else
    echo 'No modules indicated.'
fi

echo 'Verifying network interface.'
if [[ $NETWORK_INTERFACE == '' ]]
then
    IFS=$'\n'
    net_interfaces=(`ls /sys/class/net`)
    if [[ $interface_type -eq 1 ]]
    then
        IFS=' '
        fields=($HARDWARE)
        slot=${fields[0]}
        for potential_interface in "${net_interfaces[@]}"
        do
            seek_interface=`/usr/bin/find /sys/devices -type d | grep pci | grep ${potential_interface} | grep -m 1 '${slot}' | wc -c`
            if [[ seek_interface != 0 ]]
            then
                NETWORK_INTERFACE=${potential_interface}
                echo "Selected PCI interface [$NETWORK_INTERFACE]."
                break
            fi
        done
    else
        # [[ $interface_type -eq 2 ]]
        for potential_interface in "${net_interfaces[@]}"
        do
            if [[ $potential_interface == $PREFIX_WIRELESS_INTERFACE* ]]
            then
                NETWORK_INTERFACE=${potential_interface}
                echo "Selected USB interface [$NETWORK_INTERFACE]."
                break
            fi 
        done
    fi
    unset IFS
fi
if [[ $NETWORK_INTERFACE == '' ]]
then
    if [[ $interface_type -eq 1 ]]
    then
        echo 'ERROR: Network interface unknown; exiting.' 1>&2
        exit 1
    else
    # [[ $interface_type -eq 2 ]]
        echo 'ERROR: Wireless network interface not found.'
        echo 'If there has been a kernel update, you will need to rebuild the kernel module.'
        echo 'Follow the steps indicated in the build README for the existing wireless adapter.'
        echo 'As of this writing, a reboot gets the wireless interface to appear in /sys/class/net.'
        exit 1
    fi
fi

# Configure wpa_supplicant as needed
if [[ $interface_type -eq 2 ]]
then
    wpa_source_file="${SOURCE_PATH_OS}main/wpa_supplicant.conf"
    wpa_conf='/etc/wpa_supplicant.conf'
    export WIFI_SSID="$WIFI_SSID"
    export WIFI_PASSWORD="$WIFI_PASSWORD"
    envsubst \$WIFI_SSID,\$WIFI_PASSWORD < "$wpa_source_file" > "$wpa_conf"
    chown root:root "$wpa_conf"
    chmod 0644 "$wpa_conf"
fi

echo 'Updating olympus interfaces.'
interfaces_source_directory="${SOURCE_PATH_OS}main/interfaces.d"
if [[ $server_type -eq 3 ]]
then
    interfaces_source_file="${interfaces_source_directory}/ifcfg.DHCP"
else
    interfaces_source_file="${interfaces_source_directory}/ifcfg.STATIC"
fi
echo -n 'Make this the start-up network interface? Enter "Y" (yes) if so. > '
read auto_initialize
if [ "$auto_initialize" == 'Y' ] || [ "$auto_initialize" == 'y' ]
then
    find $INTERFACES_FILE_PATH -type f | xargs sed -i -e 's/^auto/# auto/g'
    auto_string="auto $NETWORK_INTERFACE"$'\n'
else
    auto_string="# auto $NETWORK_INTERFACE"$'\n'
fi
export AUTO="$auto_string"
export IP="$IP"
export NETWORK_INTERFACE="$NETWORK_INTERFACE"
export WPA_CONF=''
if [[ $interface_type -eq 2 ]]
then
    export WPA_CONF='wpa-conf /etc/wpa_supplicant.conf'
fi
INTERFACES_FILE="${INTERFACES_FILE_PATH}${INTERFACES_FILE_PREFIX}${NETWORK_INTERFACE}"
envsubst \$AUTO,\$IP,\$NETWORK_INTERFACE,\$WPA_CONF < "$interfaces_source_file" > "$INTERFACES_FILE"
chown root:root $INTERFACES_FILE
chmod 0644 $INTERFACES_FILE

get_running_interface () {
    up_interface=`/usr/bin/find /sys/class/net/*/operstate | xargs grep -l up`
    IFS=/
    read -a up_file_pieces <<< $up_interface
    unset IFS
    running_interface="${up_file_pieces[4]}"
    echo "$running_interface"
}
running_interface=$( get_running_interface )

started=false
running_ip_address=`hostname -I`
my_ip_address=`who am i | awk '{print $5}' | sed -r 's/[\(/)]//g'`

echo
echo 'NETWORKING STATUS'
echo '-----------------'
echo
if [[ $running_interface == '' ]]
then
    echo 'Active interface: None'
elif [[ $running_interface == $PREFIX_WIRELESS_INTERFACE* ]]
then
    echo 'Active interface: USB wireless'
elif [[ $running_interface == $PREFIX_ETHERNET_INTERFACE* ]]
then
    echo 'Active interface: PCI ethernet'
else
    echo 'Active interface: Unknown'
fi
if [[ $running_ip_address == '' ]]
then
    echo 'Active IP: None'
else
    echo "Active IP: $running_ip_address"
fi
startup_ip_address=''
startup_interface=`find $INTERFACES_FILE_PATH -type f | xargs grep -l '^auto'`
INTERFACES_FILE="${INTERFACES_FILE_PATH}${INTERFACES_FILE_PREFIX}${PREFIX_ETHERNET_INTERFACE}"
if [[ $startup_interface == $INTERFACES_FILE* ]]
then
    echo 'Start-up interface: PCI ethernet'
    startup_ip_address=`find $INTERFACES_FILE* | xargs grep address | awk '{print $2}'`
    echo "Start-up IP address: $startup_ip_address"
else
    INTERFACES_FILE="${INTERFACES_FILE_PATH}${INTERFACES_FILE_PREFIX}${PREFIX_WIRELESS_INTERFACE}"
    if [[ $startup_interface == $INTERFACES_FILE* ]]
    then
        echo 'Start-up interface: USB wireless'
        startup_ip_address=`find $INTERFACES_FILE* | xargs grep address | awk '{print $2}'`
        echo "Start-up IP address: $startup_ip_address"
    elif [[ $startup_interface == '' ]]
    then
        echo 'WARNING: No start-up interface configured.'
    else
        echo 'WARNING: Start-up interface unknown.'
    fi
fi

cat << EOF

SET RUNNING NETWORK
-------------------

EOF
# OPTION ONE: Do nothing
# OPTION TWO: Test existing networking

operations='1/2'
option_three=''
option_three_reboot=false
option_four=''
option_four_reboot=false
echo "1. Exit without further commands"
echo "2. Test network connectivity"

# Possible OPTION THREE
if [[ $running_interface != $PREFIX_ETHERNET_INTERFACE* ]] && [[ $running_interface != $PREFIX_WIRELESS_INTERFACE* ]]
then
    echo "3. Enable defined network interface"
    option_three='enable_network'
    operations+='/3'
elif [[ $running_interface == $PREFIX_ETHERNET_INTERFACE* ]]
then
    INTERFACES_FILE="${INTERFACES_FILE_PATH}${INTERFACES_FILE_PREFIX}${PREFIX_ETHERNET_INTERFACE}"
    if [ $startup_ip_address != $running_ip_address ] && [[ $my_ip_address =~ $IP_REGEX ]] && [ $my_ip_address != $startup_ip_address ]
    then
        if [[ $startup_interface == $INTERFACES_FILE* ]]
        then
            echo "3. Restart active PCI ethernet interface $running_interface"
            echo '   WARNING: Reboot required due to change of IP address!'
            option_three='restart_active'
            option_three_reboot=true
        fi
    else
        echo "3. Restart active PCI ethernet interface $running_interface"
        option_three='restart_active'
    fi
elif [[ $running_interface == $PREFIX_WIRELESS_INTERFACE* ]]
then
    INTERFACES_FILE="${INTERFACES_FILE_PATH}${INTERFACES_FILE_PREFIX}${PREFIX_WIRELESS_INTERFACE}"
    if [[ $startup_interface == $INTERFACES_FILE* ]]
    then
        echo "3. Restart active USB wifi interface $running_interface"
        echo '   WARNING: Reboot required due to interruption of wireless interface!'
        option_three='restart_active'
        option_three_reboot=true
    fi
fi
if [ $option_three ]
then
    operations+='/3'
fi

# Possible OPTION THREE or FOUR
if [[ $running_interface == $PREFIX_ETHERNET_INTERFACE* ]]
then
    OPTIONAL_INTERFACES_FILE="${INTERFACES_FILE_PATH}${INTERFACES_FILE_PREFIX}${PREFIX_WIRELESS_INTERFACE}"
    file_count=0
    file_count=`find $OPTIONAL_INTERFACES_FILE* | wc -l`
    if [[ $file_count -eq 1 ]]
    then
        if [ $option_three ]
        then
            option_four='switch_active'
            echo '4. Switch to USB wifi interface'
            operations+='/4'
        else
            option_three='switch_active'
            echo '3. Switch to USB wifi interface'
            operations+='/3'
        fi
    fi
    if [ $startup_ip_address != $running_ip_address ] && [[ $my_ip_address =~ $IP_REGEX ]] && [ $my_ip_address != $startup_ip_address ]
    then
        echo '   WARNING: Reboot required due to change of IP address!'
        if [ ! $option_four ]
        then
            option_three_reboot=true
        else
            option_four_reboot=true
        fi
    fi
elif [[ $running_interface == $PREFIX_WIRELESS_INTERFACE* ]]
then
    INTERFACES_FILE="${INTERFACES_FILE_PATH}${INTERFACES_FILE_PREFIX}${PREFIX_ETHERNET_INTERFACE}"
    if [[ $startup_interface == $INTERFACES_FILE* ]]
    then
        if [ $option_three ]
        then
            option_four='switch_active'
            echo '4. Switch to PCI ethernet interface'
            operations+='/4'
        else
            option_three='switch_active'
            echo '3. Switch to PCI ethernet interface'
            operations+='/3'
        fi
        echo '   WARNING: Reboot required due to interruption of wireless interface!'
        option_four_reboot=true
    fi
fi

started=false
echo
printf "Choose operation ($operations). > "
read operation_type
IFS=$'\n'
if [[ $operation_type -eq 1 ]]
then
    echo 'Bypassing further actions.'
elif [[ $operation_type -eq 2 ]]
then
    echo 'Verifying network connectivity.'
    is_up=`/usr/bin/ping -w 2 -c 1 $PING_TEST_IP | grep " 0% packet loss" | wc -l`
    if [[ $is_up -eq 1 ]]
    then
        echo "Network connection through [$running_interface] is verified."
    else
        echo "Network cannot be reached."
    fi
elif [[ $operation_type -eq 3 ]]
then
    if [ ! $option_three ]
    then
        echo 'ERROR: Bad choice; skipping further actions.'
    else
        if [[ $option_three == 'enable_network' ]]
        then
            echo
            echo 'Select interface to start:'
            echo
            available_interfaces=(`ls ${INTERFACES_FILE_PATH}`)
            enable_options=()
            index=0
            enable_option_numbers=''
            for available_interface in "${available_interfaces[@]}"
            do
                this_interface=`echo "$available_interface" | sed "s/^${INTERFACES_FILE_PREFIX}//"`
                enable_options[$index]=$this_interface
                ((index++))
                if [ ! $enable_option_numbers ]
                then
                    enable_option_numbers=$index
                else
                    enable_option_numbers+="/$index"
                fi
            done
            index=1
            choices=()
            valid_choices=()
            valid_choices[0]=''
            for enable_option in "${enable_options[@]}"
            do
                if [[ $enable_option == $PREFIX_ETHERNET_INTERFACE* ]]
                then
                    interface_description='PCI ethernet interface'
                elif [[ $enable_option == $PREFIX_WIRELESS_INTERFACE* ]]
                then
                    interface_description='USB wireless interface'
                else
                    continue
                fi
                echo "$index. $interface_description [$enable_option]" 
                choices+=($index)
                valid_choices[$index]=$enable_option
                ((index++))
            done
            echo
            printf "Choose interface ($enable_option_numbers). > "
            read selected_start_interface
            if [[ " ${choices[*]} " == *"$selected_start_interface"* ]]
            then
                to_start=${valid_choices[$selected_start_interface]}
                echo "Starting $to_start."
                ifup $to_start
                started=true
            else
                echo 'ERROR: Bad choice; skipping further actions.'
            fi
        elif $option_three_reboot
        then
            echo 'Rebooting in 5 seconds ... exiting ...'
            sleep 5
            reboot now && exit
        else # $running_interface == $PREFIX_ETHERNET_INTERFACE*
            echo 'Restarting ethernet interface ...'
            ifdown $running_interface && ifup $running_interface
            started=true
        fi
    fi
elif [[ $operation_type -eq 4 ]]
then
    if [ ! $option_four ]
    then
        echo 'ERROR: Bad choice; skipping further actions.'
    else
        if $option_four_reboot
        then
            echo 'Rebooting in 5 seconds ... exiting ...'
            sleep 5
            reboot now && exit
        else
            echo 'Switching to USB wireless interface.'
            IFS=$'\n'
            net_interfaces=(`ls /sys/class/net`)
            for potential_interface in "${net_interfaces[@]}"
            do
                if [[ $potential_interface == $PREFIX_WIRELESS_INTERFACE* ]]
                then
                    NETWORK_INTERFACE=${potential_interface}
                break
                fi 
            done
            unset IFS
            ifdown $running_interface && ifup $NETWORK_INTERFACE
            started=true
        fi
    fi
else
    echo 'ERROR: Bad choice; skipping further actions.'
fi

if $started
then
    verified=false
    echo "Verifying network."
    sleep_seconds=3
    for i in {1..30}
    do
        if [[ $i -gt 1 ]]
        then
            sleep $sleep_seconds
            echo "Retry, attempt $i of 30."
        fi
        is_up=`/usr/bin/ping -w 2 -c 1 $PING_TEST_IP | grep " 0% packet loss" | wc -l`
        if [[ $is_up -eq 1 ]]
        then
            running_interface=$( get_running_interface )
            echo "Network connection through [$running_interface] is verified."
            verified=true
            break
        elif [[ $i -lt 30 ]]
        then
            echo "Failed verification, attempt $i of 30. Will wait $sleep_seconds seconds, then retry."
        fi
    done
    if [[ $verified == false ]]
    then
        echo "ERROR: Unable to verify network connection; exiting." 1>&2
        exit 1
    fi
fi

echo 'TIP: Use "ip a" to further verify established connection; look for correct network IP under "inet".'
echo 'Success! Exiting.'
exit
