{#

Currently this shell encapsulates the steps used to complete a distro update.
Right now it's a simple list with minimal details.

For 10 to 11: https://linuxize.com/post/how-to-upgrade-debian-10-to-debian-11/

Unless noted, run steps as a privileged user under "sudo -i".

Make note of and repair errors revealed by apt and salt.

* ---------- *

salt '<server>' state.highstate -v
-- Repair any errors detected by highstate before continuing
salt '<server>' state.highstate pillar='{"pkg_latest": true}' -v
<olympus repository>/service/salt/util/package_version_repo_updater.pl
-- Update existing package specifications as identified by
   package_version_repo_updater.pl
-- Repair any errors detected by package update highstate before continuing

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade
-- The above three steps upgrade to current distro version to the latest
   available.
-- Work through issues displayed
dpkg -C
apt-mark showhold
-- Work through issues displayed

-- NETWORKING BEGIN

-- Assuming a kernel update has occurred, here it's likely that a wireless USB
   network connection will fail at reboot due to a broken or missing driver.
   Therefore, before reboot, connect ethernet and use networking.sh as
   described below to switch to the PCI ethernet connection option. A reboot
   will enable the new kernel, after which you can rebuild the wireless driver
   against the new kernel.

networking.sh
-- Located in "install/debian/scripts/" under olympus git repository.
-- Connect a networking cable between the router and eno1 and use the PCI
   ethernet option to obtain a networking connection.
reboot now
-- Upon reboot, follow the driver build steps located in
   "install/debian/etc/adapters/wireless/usb/<wireless adapter>/notes.README".
reboot now
networking.sh
-- Use the wireless networking option to enable wireless connectivity. If
   successful, you can disconnect the ethernet cable.

-- NETWORKING END

reboot now
ping 8.8.8.8
-- Test the network connection via ping of default Google DNS server.

-- STOP HERE if only upgrading to the latest version of a major release.
   The following steps are for major release upgrade (for example, Debian
   buster to Debian bullseye).
-- Review upgrade procedures for added packages. You may be required to upgrade
   versions of these packages BEFORE upgrading the major release. This is
   typically accomplished by:
   1. Upgrading respository entries that point to a specific version of an
      added package
   2. Use "apt-get update" steps indicated previously to upgrade the added
      package

-- Edit/push release and repo settings at top of distribution.sls pillar file
   (unprivileged)
-- Listing of settings ('xxx' represents a setting to change'):
   {% set release_name = 'xxx' %}
   previous-release: xxx
   release-version: xxx
-- Verify latest releases and repositories with software sources beforehand

salt '<server>' saltutil.sync_all
salt '<server>' state.sls repository
-- Rebuilds apt repository entries and keys
-- May have run error the first time. Try running again.

apt-get update
-- Rebuild package index
-- May have run error the first time. Try running again.

apt list --upgradable
-- Heads up of what's coming

DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade
-- Upgrade complete

apt install linux-headers-$(uname -r)
-- Install the new kernel headers
-- Also, edit "service/salt/pillar/distribution.sls" in the acropolis
   repository, as follows:
   1. Update the "linux_kernel" specification using the result of $(uname -r)
   2. Locate the "linux-headers-{{ linux_kernel }}" package specification and
      update the version to match that of the newly installed linux headers
      package [hint: apt list linux-headers-$(uname -r)].
   3. Commit these changes and push to git.

apt-get autoremove
-- Get rid of unused packages

apt search '~o'
-- May be useful checking for obsolete packages

-- Re-execute NETWORKING START -> NETWORKING END steps above. Note that a
   reboot may be need to enable the new kernel before rebuilding the wireless
   kernel module.

cd
olympus/service/salt/util/package_version_repo_updater.pl
-- Check output files back into git repo
-- Run as unprivileged

-- NETWORKING BEGIN

-- Due to the kernel update, follow the steps in the above NETWORKING
   BEGIN/END section as part of the reboot to enable the new kernel.

-- NETWORKING END

salt '<server>' state.highstate -v
-- Work through all errors displayed
-- Update all upgraded dependencies

-- Check for available updates to major dependencies (Django)

-- Useful salt commands for debugging:
   sudo -i salt-run fileserver.update
   sudo -i salt '*' saltutil.refresh_pillar -v
   sudo -i salt '*' saltutil.sync_all -v

#}
