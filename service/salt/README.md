# Saltstack service command hints

The following are key commands used as part of regular system maintenance and
development under SaltStack.  As indicated by the use of **sudo**, these
commands are for administrators or other users with the proper privilege.

* Reset pillar

A useful command when changes have been made to the way in which pillar values
are organized in git.

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

The sample run below illustrates the range of components updated. In particular,
"modules" is important as changes to salt modules aren't immediately available
after a git check-in.  Running this command will cause the salt master to update
module code, with the names of updated modules being echoed directly after the
*modules:* line. Note that multiple runs might be needed to display the
echoed verification; alternatively, wait 30-60 seconds after a git check-in..

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
Afterwards, run *./service/salt/util/package_version_repo_updater.pl* in a working
olympus git repository on the updated server to generate updated package
specifications in pillar files. These updated pillar files appear in "/tmp"; the
updater will identify them by name, and each file maps to a specific existing
pillar file. These newly-generated files should then be copied into the working
repository and pushed to the local git master.

* Selected configuration update

```
sudo -i salt '*' state.sls <STATENAME> -v
```

Run specified state file. Salt also will run any states which the selected state
requires.

* Machine shut-down

```
sudo -i salt '*' state.sls shutdown -v
```
```
sudo -i salt '*' state.sls shutdown pillar='{"reboot": true}' -v
```

Shut down machine with default USB backup for main local git repository and main
development user git repository clones. In the second command, the pillar
setting will cause the machine to reboot rather than shut down.

```
sudo salt '*' slsutil.renderer salt://service/salt/fs/services/frontend.sls default_render=jinja -v
```

A useful command when checking for jinja2 formatting errors. Substitute the
path and name of the file being debugged for the one in the example.
