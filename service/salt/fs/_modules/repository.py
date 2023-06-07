# -*- coding: utf-8 -*-

'''
Tools for managing apt repositories and their keys
'''

import datetime
import os
import re
import subprocess


def update_repository_key(key, url, is_gpg=False):
    if not os.path.isfile(key):
        return False
    p = subprocess.run(['/usr/bin/gpg',
                        '--show-keys',
                        key],
                       capture_output=True,
                       text=True)
    lines = p.stdout.split("\n")
    for line in lines:
        matched = re.match(r'^.*\[expires: (.*?)\].*$', line)
        if matched:
            if (datetime.datetime.today() >=
                    datetime.datetime.strptime(matched.group(1), '%Y-%m-%d')):
                os.remove(key)
                if is_gpg is True:
                    command = ('/usr/bin/curl -fsSL ' +
                               url +
                               ' | tee ' +
                               key)
                else:
                    command = ('/usr/bin/curl -fsSL ' +
                               url +
                               ' | gpg --dearmor -o ' +
                               key)
                p = subprocess.run(command, shell=True, check=True)
                if p.returncode == 0:
                    return True
                else:
                    return False
            else:
                return True
