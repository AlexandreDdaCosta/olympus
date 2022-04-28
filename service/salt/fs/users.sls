{% for groupname in pillar.get('groups') %}
{{ groupname }}:
  group:
    - present
{% endfor %}

{% for username, user in pillar.get('users', {}).items() %}
{% if 'server' not in user or grains.get('server') in user['server'] -%}
{{ username }}:

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
      {%- endfor %}
      {%- endif %}
    {% if 'createhome' in user and user['createhome'] -%}
    - home: /home/{{ username }}
    {%- endif %}
    - name: {{ username }}
    - present
    {% if 'shell' in user -%}
    - shell: {{ user['shell'] }}
    {%- endif %}

{% if 'createhome' in user and user['createhome'] and 'ssh_public_key' in user %}
{{ username }}-sshconfig:

  file.directory:
    - dir_mode: 0700
    - group: {{ username }}
    - name: /home/{{ username }}/.ssh
    - user: {{ username }}
  file.managed:
    - group: {{ username }}
    - mode: 0644
    - name: /home/{{ username }}/.ssh/config
    - user: {{ username }}
    - source: salt://users/.ssh/config.jinja
    - template: jinja

{{ username }}-sshkey:

  file.managed:
    - contents: {{ user['ssh_public_key'] }}
    - group: {{ username }}
    - mode: 0750
    - name: /home/{{ username }}/.ssh/authorized_keys
    - user: {{ username }}

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
