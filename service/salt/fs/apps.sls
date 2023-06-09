include:
  - base: services.bigdata

{# Sanity check for inattentive administrators #}
{% if 'apps' in pillar['servers'][grains.get('server')] %}

{% for packagename, package in pillar.get('apps-pip3-packages', {}).items() %}
{{ packagename }}:
  pip.installed:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - name: {{ packagename }}
    - upgrade: True
{% elif package != None and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - name: {{ packagename }} {{ package['version'] }}
    {% else %}
    - name: {{ packagename }}
    {% endif %}
{% else %}
    - name: {{ packagename }}
{% endif %}
    - bin_env: '/usr/bin/pip3'
{% endfor %}

/usr/lib/tmpfiles.d/olympus.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://apps/olympus.conf.jinja
    - template: jinja
    - user: root

manage_tmpfiles:
  cmd.run:
    - name: 'systemd-tmpfiles --create --remove'
    - watch:
        - file: /usr/lib/tmpfiles.d/olympus.conf

{% set apps = pillar['servers'][grains.get('server')]['apps'] + [ pillar['core-app-user'] ] %}
{% for app in apps %}
{% if app !=  pillar['core-app-user'] %}
app_user_{{ app }}:
  group:
    - name: {{ app }}
    - present
  user:
    - createhome: True
    - fullname: {{ app }}
    - home: /home/{{ app }}
    - name: {{ app }}
    - present
    - shell: /bin/false
    - groups:
      - {{ app }}

/home/{{ app }}:
  file.recurse:
    - dir_mode: 0755
    - exclude_pat: lib/* 
    - file_mode: 0644
    - group: {{ app }}
    - require:
      - sls: services.bigdata
    - source: salt://apps/{{ app }}
    - user: {{ app }}
  cmd.run:
    - name: 'if [ -d "/home/{{ app }}/bin" ]; then chmod -R 0750 /home/{{ app }}/bin; fi'

/home/{{ app }}-perms:
  cmd.run:
    - name: 'chmod 0750 /home/{{ app }}'

{{ pillar['olympus-app-package-path'] }}/{{ app }}:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://apps/{{ app }}/lib
    - user: root
  cmd.run:
    - name: "find {{ pillar['olympus-app-package-path'] }}/{{ app }} -type f | grep -E 'test/.*?\\.py$' | xargs -r chmod 0755"

/home/{{ app }}/etc:
  file.directory:
    - dir_mode: 0700
    - group: {{ app }}
    - name: /home/{{ app }}/etc
    - user: {{ app }}
{% endif %}

/home/{{ app }}/Downloads:
  file.directory:
    - group: {{ app }}
    - makedirs: False
    - mode: 0750
    - user: {{ app }}
{% endfor %}

{% endif %}
