{% set trim_blocks=True %}
{% for groupname, group in pillar.get('groups', {}).items() %}
{{ groupname }}-group:
  group:
    - name: {{ groupname }}
{% if 'gid' in group %}
    - gid: {{ group['gid'] }}
{% endif %}
    - present
{% endfor %}

{% for username, user in pillar.get('users', {}).items() %}
{% if 'server' not in user or grains.get('server') in user['server'] %}
{% if 'edit_precommand' in user %}
edit_precommand_{{ username }}:
  cmd.run:
    - name: {{ user['edit_precommand'] }}
{% endif %}

user_{{ username }}:

{% if 'gid' not in user %}
  group:
    - name: {{ username }}
    - present
{% endif %}
  user:
    {% if 'createhome' in user and user['createhome'] %}
    - createhome: True
    {%- endif %}
    {% if 'fullname' in user %}
    - fullname: {{ user['fullname'] }}
    {%- endif %}
{% if 'gid' in user %}
    - gid: {{ user['gid'] }}
{% endif %}
{% if 'uid' in user %}
    - uid: {{ user['uid'] }}
{% endif %}
    - groups:
{% if 'gid' not in user %}
      - {{ username }}
{% endif %}
      {% if 'is_staff' in user and user['is_staff'] %}
      - git
      - staff
      {% endif %}
      {% if 'groups' in user %}
      {% for groupname in user['groups'] %}
      - {{ groupname }}
      {% endfor %}
      {% endif %}
    {% if 'createhome' in user and user['createhome'] %}
    - home: /home/{{ username }}
    {% endif %}
    - name: {{ username }}
    - present
    {% if 'shell' in user %}
    - shell: {{ user['shell'] }}
    {% elif 'class' in user and user['class'] == "human" %}
    - shell: /bin/bash
    {% else -%}
    - shell: /usr/sbin/nologin
    {%- endif %}
    {% if 'class' in user and user['class'] == "system" %}
    - system: True
    {% endif %}

{% if 'createhome' in user and user['createhome'] %}
/home/{{ username }}-perms:
  cmd.run:
    - name: 'chmod 0750 /home/{{ username }}'

{{ username }}-etc:
  file.directory:
    - dir_mode: 0700
    - group: {{ username }}
    - name: /home/{{ username }}/etc
    - user: {{ username }}

{% endif %}
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

{% endif %}
{% endif %}
{% endfor %}
