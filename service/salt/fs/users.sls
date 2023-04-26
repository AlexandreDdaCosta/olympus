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

{{ username }}-ssh-agent.service:
  file.managed:
    - dir_mode: 0750
    - group: {{ username }}
    - makedirs: True
    - mode: 0640
    - name: /home/{{ username }}/.config/systemd/user/ssh-agent.service
    - source: salt://users/.ssh/files/ssh-agent.service
    - user: {{ username }}

{{ username }}-config-systemd-user-dir:
  cmd.run:
    - name: find /home/{{ username }}/.config/systemd -type d | xargs chmod 0750

{{ username }}-ssh_auth_socket.conf:
  file.managed:
    - dir_mode: 0750
    - group: {{ username }}
    - makedirs: True
    - mode: 0640
    - name: /home/{{ username }}/.config/environment.d/ssh_auth_socket.conf
    - source: salt://users/.ssh/files/ssh_auth_socket.conf
    - user: {{ username }}

{{ username }}-config-environment.d-dir:
  cmd.run:
    - name: find /home/{{ username }}/.config/environment.d -type d | xargs chmod 0750

{%- endif %}
{% if 'createhome' in user and user['createhome'] and 'vimuser' in user and user['vimuser'] -%}
{{ username }}-vimrc:
  file.managed:
    - group: {{ username }}
    - mode: 0640
    - name: /home/{{ username }}/.vimrc
    - user: {{ username }}
    - source: salt://users/vimrc.jinja
    - template: jinja
{%- endif %}

{% endif %}
{% endfor %}
