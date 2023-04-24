# Saltstack service command hints

The following are key commands used as part of regular system maintenance and development under Saltstack.
As indicated by the use of **sudo**, these are for the use of administrative users with the proper privilege.

* Reset pillar

A useful command when changes have been made to the way in which pillar values are organized in git.

```
sudo -i salt '*' saltutil.refresh_pillar -v
```

Sample run:

```
alex@zeus:~$ sudo -i salt '*' saltutil.refresh_pillar -v
Executing job with jid 20230424033127175816
-------------------------------------------

zeus:
    True
```

* Update salt components

```
sudo -i salt '*' saltutil.sync_all -v
```

The sample run below illustrates the variety of components updated. In particular, "modules"
is important as changes to salt modules are not immediately available after a git check-in.
Running this command will cause the salt master to update module code, with the updated
modules being listed directly after the *modules:* line.

```
alex@zeus:~$ sudo -i salt '*' saltutil.sync_all -v
Executing job with jid 20230424033054122463
-------------------------------------------

zeus:
    ----------
    beacons:
    clouds:
    engines:
    executors:
    grains:
    log_handlers:
    matchers:
    modules:
    output:
    proxymodules:
    renderers:
    returners:
    sdb:
    serializers:
    states:
    thorium
```

* Global configuration update for all minions

```
sudo -i salt '*' state.highstate -v
```
```
sudo -i salt '*' state.highstate pillar='{"pkg_latest": true}' -v
```

The pillar setting forces all installed packages to update to latest versions.
Afterwards, run *./service/salt/util/package_version_repo_updater.pl* in a working olympus
git repository on the updated server to generate updated package specifications in
pillar files. These updated pillar files appear in "/tmp"; the updater will identify
them by name, and each file maps to a specific existing pillar file. These newly-generated
files should then be copied into the working repository and pushed to the local git
master.

* Selected configuration update

```
sudo -i salt '*' state.sls <STATENAME> -v
```

Run specified state file. Salt also will run any states which the selected state requires.

* Machine shut-down

```
sudo -i salt '*' state.sls shutdown -v
```
```
sudo -i salt '*' state.sls shutdown pillar='{"reboot": true}' -v
```

Shutdown machine with default USB backup for main local git repository and main development user
git repository clones. The pillar setting will cause the machine to reboot rather than shut down.
