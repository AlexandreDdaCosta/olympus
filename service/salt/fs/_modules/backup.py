# -*- coding: utf-8 -*-

'''
Manage data backup and restoration
'''

import re, os, shutil, subprocess, time

def usb_backup_olympus():
    user = __salt__['pillar.get']('core-staff-user')
    # Verify presence of olympus USB
    cmd = "blkid"
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
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
    mount_directory = '/media/usb_backup_olympus_' + str(int(time.time()))
    os.mkdir(mount_directory)
    cmd = "mount " + partition + " " + mount_directory
    p = subprocess.check_call(cmd,shell=True)
    # Git repository
    dir = mount_directory + '/BAK/repository'
    sourcedir = '/home/git/repository'
    os.rename(dir,dir + '.bak')
    shutil.copytree(sourcedir,dir)
    # Working git directory
    dir = mount_directory + '/BAK/olympus'
    sourcedir = '/home/' + user + '/olympus'
    os.rename(dir,dir + '.bak')
    shutil.copytree(sourcedir,dir)
    # Debian installation files
    dir = mount_directory + '/debian8'
    sourcedir = '/home/' + user + '/olympus/install/debian8'
    os.rename(dir,dir + '.bak')
    shutil.copytree(sourcedir,dir)

    # Unmount USB
    cmd = "umount " + partition + " " + mount_directory
    p = subprocess.check_call(cmd,shell=True)
    os.rmdir(mount_directory)
    return True
