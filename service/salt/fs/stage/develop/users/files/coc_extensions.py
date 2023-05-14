#!/usr/bin/env python3

# Updates user's coc.nvim extensions

import getpass
import os

coc_extensions_jsonfile_username = None
script_username = getpass.getuser()
if (script_username == 'root'):
    coc_extensions_jsonfile_username = '/root/.config/coc/coc_extensions.json'
else:
    coc_extensions_jsonfile_username = ('/home/' +
                                        script_username +
                                        '.config/coc/coc_extension.json')
if (not os.path.isfile(coc_extensions_jsonfile_username)):
    raise Exception('coc.nim json file note found: ' +
                    coc_extensions_jsonfile_username)
