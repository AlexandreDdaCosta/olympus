# -*- coding: utf-8 -*-

'''
Manage data backup and restoration
'''

import re, os, subprocess, time

def usb_backup_olympus():
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
    #cmd = "/usr/local/bin/killserver.sh"
    #p = subprocess.check_call(cmd,shell=True)
    return True
