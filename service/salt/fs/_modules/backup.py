# -*- coding: utf-8 -*-

'''
Manage data backup and restoration
'''

import re, os, shutil, subprocess, time

def usb_backup_olympus():
    user = __salt__['pillar.get']('core-staff-user')
    if user is None:
        raise Exception("Can't get core-staff-user from pillar.")
    # Verify presence of olympus USB
    cmd = "blkid"
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,text=True)
    output = p.communicate()
    lines = output[0].split("\n")
    matchstring = '.*' + re.escape('LABEL="olympus"') + '.*'
    partition = None
    for line in lines:
        if re.match(matchstring,line):
            partition = re.sub(r"([^\:]*)\:.*$", r"\1", line.strip())
            break
    if partition is None:
        raise Exception('USB drive for olympus backup not detected.')

    # Mount USB
    mount_directory = '/media/usb_backup_olympus_' + str(int(time.time()))
    os.mkdir(mount_directory)
    cmd = "mount " + partition + " " + mount_directory
    p = subprocess.check_call(cmd,shell=True)

    # Make backups
    # Git repository
    _backup_directory(mount_directory + '/BAK/repository', '/home/git/repository')
    # Working git directory
    _backup_directory(mount_directory + '/BAK/olympus', '/home/' + user + '/olympus')
    # Debian installation files
    _backup_directory(mount_directory + '/install', '/home/' + user + '/olympus/install')
    cmd = "chown -R " + user + ":" + user + " " + mount_directory
    p = subprocess.check_call(cmd,shell=True)

    # Unmount partition
    cmd = "umount " + mount_directory
    p = subprocess.check_call(cmd,shell=True)
    os.rmdir(mount_directory)
    return True

def _backup_directory(target, source):
    if not os.path.isdir(source):
        raise Exception(source + " not found");
    if os.path.exists(target):
        os.rename(target,target + '.bak')
    shutil.copytree(source,target)
    if os.path.exists(target + '.bak'):
        shutil.rmtree(target + '.bak')
