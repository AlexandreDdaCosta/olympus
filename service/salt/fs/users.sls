{% for groupname in pillar.get('groups') %}
{{ groupname }}-group:
  group:
    - name: {{ groupname }}
    - present
{% endfor %}

{% for username, user in pillar.get('users', {}).items() %}
{% if 'server' not in user or grains.get('server') in user['server'] -%}
{% if 'edit_precommand' in user -%}
edit_precommand_{{ username }}:
  cmd.run:
    - name: {{ user['edit_precommand'] }}
{% endif -%}

user_{{ username }}:

  group:
    - name: {{ username }}
    - present
  user:
    {% if 'createhome' in user and user['createhome'] -%}
    - createhome: True
    {%- endif %}
    {% if 'fullname' in user -%}
    - fullname: {{ user['fullname'] }}
    {%- endif %}
    - groups:
      - {{ username }}
      {% if 'is_staff' in user and user['is_staff'] -%}
      - git
      - staff
      {%- endif %}
      {% if 'groups' in user -%}
      {% for groupname in user['groups'] -%}
      - {{ groupname }}
      {% endfor %}
      {%- endif %}
    {% if 'createhome' in user and user['createhome'] -%}
    - home: /home/{{ username }}
    {%- endif %}
    - name: {{ username }}
    - present
    {% if 'shell' in user -%}
    - shell: {{ user['shell'] }}
    {%- endif %}

{% if 'createhome' in user and user['createhome'] -%}
/home/{{ username }}-perms:
  cmd.run:
    - name: 'chmod 0750 /home/{{ username }}'

{{ username }}-etc:
  file.directory:
    - dir_mode: 0700
    - group: {{ username }}
    - name: /home/{{ username }}/etc
    - user: {{ username }}

{%- endif %}
{% if 'createhome' in user and user['createhome'] and 'ssh_public_key' in user %}
{{ username }}-sshdir:
  file.directory:
    - dir_mode: 0700
    - group: {{ username }}
    - name: /home/{{ username }}/.ssh
    - user: {{ username }}

{{ username }}-sshconfig:
  file.managed:
    - group: {{ username }}
    - mode: 0640
    - name: /home/{{ username }}/.ssh/config
    - user: {{ username }}
    - source: salt://users/.ssh/config.jinja
    - template: jinja

{{ username }}-sshkey:
  file.managed:
    - contents: {{ user['ssh_public_key'] }}
    - group: {{ username }}
    - mode: 0640
    - name: /home/{{ username }}/.ssh/authorized_keys
    - user: {{ username }}

{%- endif %}
{% if 'createhome' in user and user['createhome'] and 'vimuser' in user and user['vimuser'] -%}

{{ username }}-vim:
  file.directory:
    - group: {{ username }}
    - mode: 0750
    - name: /home/{{ username }}/.vim
    - user: {{ username }}

{{ username }}-vim-bundle:
  file.directory:
    - group: {{ username }}
    - mode: 0750
    - name: /home/{{ username }}/.vim/bundle
    - user: {{ username }}

{{ username }}-vimrc:
  file.managed:
    - group: {{ username }}
    - mode: 0640
    - name: /home/{{ username }}/.vimrc
    - user: {{ username }}
    - source: salt://users/vimrc.jinja
    - template: jinja

{% for username, user in pillar.get('users', {}).items() %}
{% for vimpackagename, vimpackage in pillar.get('vim-packages', {}).items() %}
{{ username }}-vim-{{ vimpackagename}}:
{% if salt['file.directory_exists']('/home/' + username + '/.vim/bundle/' + vimpackagename) %}
  cmd.run:
    - cwd: /home/{{ username }}/.vim/bundle/{{ vimpackagename }}
{% if 'git-flags' in vimpackage -%}
    - name: sudo su -s /bin/bash -c 'git pull {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}' {{ username }}
{% else %}
    - name: sudo su -s /bin/bash -c 'git pull {{ vimpackage['repo'] }}' {{ username }}
{% endif %}
{% else %}
  cmd.run:
    - cwd: /home/{{ username }}/.vim/bundle
{% if 'git-flags' in vimpackage -%}
    - name: sudo su -s /bin/bash -c 'git clone {{ vimpackage['git-flags'] }} {{ vimpackage['repo'] }}' {{ username }}
{% else %}
    - name: sudo su -s /bin/bash -c 'git clone {{ vimpackage['repo'] }}' {{ username }}
{% endif %}
{% endif %}
{% endfor %}

{%- endif %}

{% endif %}
{% endfor %}
