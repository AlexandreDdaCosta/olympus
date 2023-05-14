#!/usr/bin/env python3

# Updates user's coc.nvim extensions

import getpass
import json
import os
import re
import subprocess

# Read json configuration file

script_username = getpass.getuser()
if (script_username == 'root'):
    coc_extensions_filename = '/root/.config/coc/coc_extensions.json'
    coc_packages_filename = '/root/.config/coc/extensions/package.json'
else:
    coc_extensions_filename = ('/home/' +
                               script_username +
                               '/.config/coc/coc_extensions.json')
    coc_packages_filename = ('/home/' +
                             script_username +
                             '/.config/coc/extensions/package.json')
if (not os.path.isfile(coc_extensions_filename)):
    raise Exception('User coc.nvim extensions file not found: ' +
                    coc_extensions_filename)
try:
    with open(coc_extensions_filename) as coc_extensions_file:
        extensions_file_contents = coc_extensions_file.read()
    parsed_extensions_file = json.loads(extensions_file_contents)
except Exception:
    raise Exception('Error while reading coc.nvim extensions file.')

# If package.json exists, read it for installed extensions

installed_packages = {}
try:
    with open(coc_packages_filename) as coc_packages_file:
        packages_file_contents = coc_packages_file.read()
    parsed_packages_file = json.loads(packages_file_contents)
    for package in parsed_packages_file['dependencies']:
        version = re.sub('[^0-9.]',
                         '',
                         parsed_packages_file['dependencies'][package])
        installed_packages[package] = version
except FileNotFoundError:
    installed_packages = {}
except Exception:
    raise Exception('Error while reading package.json for installed ' +
                    'coc extensions.')

# Install missing coc.nvim extensions as needed
# Reinstall coc.nvim extensions with incorrect version

install_errors = 0
for extension in parsed_extensions_file:
    if extension not in installed_packages:
        print('Installing missing extension ' + extension)
    elif parsed_extensions_file[extension] != installed_packages[extension]:
        print('Reinstalling extension ' + extension + '; version mismatch.')
    else:
        print('Extension ' +
              extension +
              ' already installed and is the correct version.')
        continue
    command = ('sudo su -s /bin/bash -c ' +
               '"/usr/bin/vim -c ' +
               "'CocInstall -sync " +
               extension +
               '@' +
               parsed_extensions_file[extension] +
               '|q\'" ' +
               script_username)
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print('Exception thrown during installation of extension ' +
              extension +
              ': Error code ' +
              str(e.returncode))
        install_errors = install_errors + 1
if install_errors > 0:
    exit(1)
exit(0)
