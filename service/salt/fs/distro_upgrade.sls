{#

Currently this shell encapsulates the steps used to complete a distro update. Right now
it's a simple list with minimal details.

See https://linuxconfig.org/how-to-upgrade-debian-9-stretch-to-debian-10-buster.

Unless noted, run steps as a privileged user under "sudo -i".

Make note of and repair errors revealed by apt and salt.

* ---------- *

apt-get update
apt-get upgrade
apt-get dist-upgrade
-- May need to run wireless.sh from install (networking issues)

dpkg -C
apt-mark showhold
-- Work through issues displayed

Edit/push release and repo settings in distribution.sls pillar file (unprivileged)
-- Verify latest releases and repositories with software sources beforehand

salt '<server>' state.sls repository
-- Rebuilds apt repository entries and keys

apt-get update
-- Rebuild package index

apt list --upgradable
-- Heads up of what's coming

apt-get upgrade
apt-get dist-upgrade
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
