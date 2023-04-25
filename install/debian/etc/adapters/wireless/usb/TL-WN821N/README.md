# Wireless USB driver for olympus

The latest version of this driver was built on a Debian 11 system using an
open-source driver for the Realtek RTL8192EU software used to drive a specific
wireless dongle. The target server is a Dell Poweredge R140 without built-in
wireless.

Once the system has been set up and running, these instructions can be used
to rebuild the driver in the event of a kernel upgrade. Start with installing
the headers for the new kernel. It's also a good idea to be sure that the 
build kit is fully up-to-date.

Build steps for user "root":

## Install latest Debian and enable networking

For this step, use an on-board ethernet adapter and connect the machine it to
the local network.

## Verify entries in /etc/apt/sources.list and /etc/apt/sources.list.d

Right after a USB installation, /etc/apt/sources.list points to the USB drive.
A networked version of this file:

``` 
deb http://ftp.us.debian.org/debian/ <Debian release nickname> main contrib
deb-src http://ftp.us.debian.org/debian/ <Debian release nickname> main contrib
deb http://ftp.us.debian.org/debian/ <Debian release nickname>-updates main contrib
deb-src http://ftp.us.debian.org/debian/ <Debian release nickname>-updates main contrib
deb http://security.debian.org/ <Debian release nickname>/updates main contrib
deb-src http://security.debian.org/ <Debian release nickname>/updates main contrib
```

## Install build kit

```
apt-get install gcc-10 git build-essential
```

## Install kernel headers

```
apt-get install linux-headers-$(uname -r)
```

## Clone the open-source driver repository from Github

```
git clone https://github.com/clnhub/rtl8192eu-linux.git
```

**TIP**: Change directory to */tmp* before cloning repository.

## Build, and install the new kernel module

```
cd rtl8192eu-linux
make
make install
```

After a successful build, the make directory will include *8192eu.ko*, which
is the new kernel module.

## Activate the new kernel module

```
modprobe 8192eu
```

## Verify the activated module by listing network interfaces

```
ls /sys/class/net
```

With the wireless adapter connected, the interface is listed as *wlxd0374568a96a*
or similar. **NOTE**: *wlx* is the Debian prefix for wireless network interfaces.
