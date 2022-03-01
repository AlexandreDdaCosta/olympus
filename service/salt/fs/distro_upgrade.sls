{#

Currently this shell encapsulates the steps used to complete a distro update. Right now
it's a simple list with minimal details.

See https://linuxconfig.org/how-to-upgrade-debian-9-stretch-to-debian-10-buster.
For 10 to 11: https://linuxize.com/post/how-to-upgrade-debian-10-to-debian-11/

Unless noted, run steps as a privileged user under "sudo -i".

Make note of and repair errors revealed by apt and salt.

* ---------- *

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade
dpkg -C
apt-mark showhold
-- Work through issues displayed
reboot now

ping 8.8.8.8
-- Test the network connection via ping of default Google DNS server.
(Here it's probable that a wireless USB network connection will fail due to a broken or missing driver. If
this is the case, proceed through the following steps:

networking.sh
-- Located in "install/debian/scripts/" under olympus git repository.
-- If the USB wifi setup succeeds, proceed to the next section (not likely due to upgraded distro)
-- If the USB wifi setup fails:
   1. Connect a networking cable between the router and eno1 and use the PCI ethernet option to obtain a 
      networking connection.
   2. Follow the driver build steps located in "install/debian/etc/adapters/wireless/usb/<wireless adapter>/notes.README",
      taking into account changes needed to accomodate the new distro. Be sure to update this README for the new distro and
      check the file back into git.
)

Edit/push release and repo settings at top of distribution.sls pillar file (unprivileged)
-- Listing of settings ('xxx' represents a setting to change'):
   {% set release_name = 'xxx' %}
   mongo-repo: xxx
   nodejs-repo: xxx
   previous-release: xxx
   release-version: xxx
   {% set python3 = xxx %}
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

apt-get autoremove
-- Get rid of unused packages

aptitude search '~o'
-- May be useful checking for obsolete packages

cd
olympus/service/salt/util/package_version_repo_updater.pl
-- Check output files back into git repo
-- Run as unprivileged

salt '<server>' state.highstate -v
-- Update all upgraded dependencies

-- Check for available updates to major dependencies (Django)

Useful salt commands for debugging:

sudo -i salt-run fileserver.update
sudo -i salt '*' saltutil.refresh_pillar -v
sudo -i salt '*' saltutil.sync_all -v

#}
