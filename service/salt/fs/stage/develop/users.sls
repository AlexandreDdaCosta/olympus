include:
  - base: users

/usr/local/bin/olympus/coc_extensions.py:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/users/files/coc_extensions.py
    - user: root

{% for username, user in pillar.get('users', {}).items() %}
{% if 'server' not in user or grains.get('server') in user['server'] -%}

{% if 'createhome' in user and user['createhome'] and 'vimuser' in user and user['vimuser'] -%}

"{{ username }}-vim":
  file.directory:
    - group: {{ username }}
    - mode: 0750
    - name: /home/{{ username }}/.vim
    - user: {{ username }}

"{{ username }}-vim-bundle":
  file.directory:
    - group: {{ username }}
    - mode: 0750
    - name: /home/{{ username }}/.vim/bundle
    - user: {{ username }}

"{{ username }}-config":
  file.directory:
    - group: {{ username }}
    - mode: 0700
    - name: /home/{{ username }}/.config
    - user: {{ username }}

"{{ username }}-coc-config":
  file.directory:
    - group: {{ username }}
    - mode: 0700
    - name: /home/{{ username }}/.config/coc
    - user: {{ username }}

"{{ username }}-vimrc":
  file.managed:
    - group: {{ username }}
    - mode: 0640
    - name: /home/{{ username }}/.vimrc
    - user: {{ username }}
    - source: salt://stage/develop/users/files/vimrc
    - template: jinja

{% for vimpackagename, vimpackage in pillar.get('develop-vim-packages', {}).items() %}
"{{ username }}-vim-{{ vimpackagename }}":
{% if salt['file.directory_exists']('/home/' + username + '/.vim/bundle/' + vimpackagename) %}
  cmd.run:
    - cwd: /home/{{ username }}/.vim/bundle/{{ vimpackagename }}
{% if 'git-flags' in vimpackage %}
    - name: sudo su -s /bin/bash -c 'git pull {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}' {{ username }}
{% elif 'git-pull-command' in vimpackage %}
    - name: sudo su -s /bin/bash -c '{{ vimpackage['git-pull-command'] }}' {{ username }}
{% else %}
    - name: sudo su -s /bin/bash -c 'git pull {{ vimpackage['repo'] }}' {{ username }}
{% endif %}
{% else %}
  cmd.run:
    - cwd: /home/{{ username }}/.vim/bundle
{% if 'git-flags' in vimpackage %}
    - name: sudo su -s /bin/bash -c 'git clone {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}' {{ username }}
{% elif 'git-clone-flags' in vimpackage %}
    - name: sudo su -s /bin/bash -c 'git clone {{ vimpackage['git-clone-flags'] }} {{ vimpackage['repo'] }}' {{ username }}
{% else %}
    - name: sudo su -s /bin/bash -c 'git clone {{ vimpackage['repo'] }}' {{ username }}
{% endif %}
{% endif %}
{% endfor %}

"/home/{{ username }}/.config/coc/coc_extensions.json":
  file.managed:
    - group: {{ username }}
    - mode: 0440
    - source: salt://stage/develop/users/coc_extensions.json.jinja
    - template: jinja
    - user: {{ username }}

{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
update-coc-nvim-extensions:
  cmd.run:
    - cwd: /home/{{ username }}/.config/coc
    - name: sudo su -s /bin/bash -c "/usr/bin/vim -c 'CocUpdateSync|q'" {{ username }}
{% else %}
"coc-nvim-extensions-{{ username }}":
  cmd.run:
    - cwd: /home/{{ username }}/.config/coc
    - name: sudo su -s /bin/bash -c "/usr/local/bin/olympus/coc_extensions.py" {{ username }}
{% endif %}

{% endif %}

{% endif %}
{% endfor %}

# For those times in development when editing under sudo just makes things easier.

root-vim:
  file.directory:
    - group: root
    - mode: 0750
    - name: /root/.vim
    - user: root

root-vim-bundle:
  file.directory:
    - group: root
    - mode: 0750
    - name: /root/.vim/bundle
    - user: root

root-config:
  file.directory:
    - group: root
    - mode: 0700
    - name: /root/.config
    - user: root

root-coc-config:
  file.directory:
    - group: root
    - mode: 0700
    - name: /root/.config/coc
    - user: root

root-vimrc:
  file.managed:
    - group: root
    - mode: 0640
    - name: /root/.vimrc
    - user: root
    - source: salt://stage/develop/users/files/vimrc
    - template: jinja

{% for vimpackagename, vimpackage in pillar.get('develop-vim-packages', {}).items() %}
root-vim-{{ vimpackagename }}:
{% if salt['file.directory_exists']('/root/.vim/bundle/' + vimpackagename) %}
  cmd.run:
    - cwd: /root/.vim/bundle/{{ vimpackagename }}
{% if 'git-flags' in vimpackage %}
    - name: git pull {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}
{% elif 'git-pull-command' in vimpackage %}
    - name: {{ vimpackage['git-pull-command'] }}
{% else %}
    - name: git pull {{ vimpackage['repo'] }}
{% endif %}
{% else %}
  cmd.run:
    - cwd: /root/.vim/bundle
{% if 'git-flags' in vimpackage %}
    - name: git clone {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}
{% elif 'git-clone-flags' in vimpackage %}
    - name: git clone {{ vimpackage['git-clone-flags'] }} {{ vimpackage['repo'] }}
{% else %}
    - name: git clone {{ vimpackage['repo'] }}
{% endif %}
{% endif %}
{% endfor %}

/root/.config/coc/coc_extensions.json:
  file.managed:
    - group: root
    - mode: 0440
    - source: salt://stage/develop/users/coc_extensions.json.jinja
    - template: jinja
    - user: root

{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
update-coc-nvim-extensions-root:
  cmd.run:
    - cwd: /root/.config/coc
    - name: sudo su -s /bin/bash -c "/usr/bin/vim -c 'CocUpdateSync|q'" root
{% else %}
coc-nvim-extensions-root:
  cmd.run:
    - cwd: /root/.config/coc
    - name: /usr/local/bin/olympus/coc_extensions.py
{% endif %}
