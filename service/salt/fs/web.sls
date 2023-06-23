include:
  - base: package

{% for packagename, package in pillar.get('web-packages', {}).items() %}
{{ packagename }}-web:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or 'version' not in package %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
    - name: {{ packagename }}
{% if 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('web-pip3-packages', {}).items() %}
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
    - require:
      - sls: package
{% endfor %}

{{ pillar.www_path }}:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

nginx:
  service.running:
    - watch:
      - file: /etc/nginx/conf.d/default.conf
  file.managed:
    - name: /etc/nginx/conf.d/default.conf
    - source: salt://web/files/default.conf

{{ pillar['web_daemon_vassals_directory'] }}:
  file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

/etc/{{ pillar['frontend_user'] }}.ini:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/frontend/files/{{ pillar['frontend_user'] }}.ini
    - user: root

/etc/rc0.d/K01{{ pillar['frontend_user'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['frontend_user'] }}

/etc/rc1.d/K01{{ pillar['frontend_user'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['frontend_user'] }}

/etc/rc2.d/S01{{ pillar['frontend_user'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['frontend_user'] }}

/etc/rc3.d/S01{{ pillar['frontend_user'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['frontend_user'] }}

/etc/rc4.d/S01{{ pillar['frontend_user'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['frontend_user'] }}

/etc/rc5.d/S01{{ pillar['frontend_user'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['frontend_user'] }}

/etc/rc6.d/K01{{ pillar['frontend_user'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['frontend_user'] }}

/etc/init.d/{{ pillar['frontend_user'] }}:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/frontend/files/init.{{ pillar['frontend_user'] }}
    - user: root

/var/log/{{ pillar['frontend_user'] }}:
  file.directory:
    - group: {{ pillar['frontend_user'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['frontend_user'] }}

/var/log/{{ pillar['frontend_user'] }}/{{ pillar['frontend_user'] }}.log:
  file.managed:
    - group: {{ pillar['frontend_user'] }}
    - mode: 0644
    - replace: False
    - user: {{ pillar['frontend_user'] }}

/etc/logrotate.d/{{ pillar['frontend_user'] }}:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/frontend/files/logrotate.{{ pillar['frontend_user'] }}
    - user: root

web-{{ pillar['frontend_user'] }}:
  service.running:
    - enable: True
    - name: {{ pillar['frontend_user'] }}
    - watch:
      - file: /etc/init.d/{{ pillar['frontend_user'] }}
