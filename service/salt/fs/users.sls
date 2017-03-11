include:
  - base: security

{% for username, user in pillar.get('users', {}).items() %}
{{ username }}:

  group:
    - name: {{ username }}
    - present
  user:
    - fullname: {{ user['fullname'] }}
    - groups:
      - {{ username }}
      {% if user['is_staff'] -%}
      - staff
      {%- endif %}
    - home: /home/{{ username }}
    - name: {{ username }}
    - present
  file.directory:
    - dir_mode: 0700
    - group: {{ username }}
    - name: /home/{{ username }}/.ssh
    - user: {{ username }}

{{ username }}-sshconfig:

  file.managed:
    - group: {{ username }}
    - mode: 0644
    - name: /home/{{ username }}/.ssh/config
    - user: {{ username }}
    - source: salt://users/.ssh/config.jinja
    - template: jinja

{% if 'ssh_public_key' in user %}
{{ username }}-sshkey:

  file.managed:
    - contents: {{ user['ssh_public_key'] }}
    - group: {{ username }}
    - mode: 0750
    - name: /home/{{ username }}/.ssh/authorized_keys
    - user: {{ username }}

{{ username }}-vimrc:

  file.managed:
    - group: {{ username }}
    - mode: 0640
    - name: /home/{{ username }}/.vimrc
    - user: {{ username }}
    - source: salt://users/vimrc.jinja
    - template: jinja

{% endfor %}
