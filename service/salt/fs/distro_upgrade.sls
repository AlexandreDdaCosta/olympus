{#

Currently this shell encapsukates the steps used to complete a distro update. Right now
it's a simple list with minimal details.

See https://linuxconfig.org/how-to-upgrade-debian-8-jessie-to-debian-9-stretch

apt-get update
apt-get upgrade
apt-get dist-upgrade
-- Check for issues
-- May need to run wireless.sh from install (networking issues)

dpkg -C
apt-mark showhold
-- Work through issues displayed

Edit release/repo settings in distribution.sls pillar file

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

salt '<server>' state.highstate
-- Update all upgraded dependencies

-- Check for available updates to major dependencies (Django)

#}
