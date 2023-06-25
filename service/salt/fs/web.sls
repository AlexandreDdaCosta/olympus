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

/etc/{{ pillar['web_daemon'] }}.ini:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://web/{{ pillar['web_daemon'] }}.ini.jinja
    - template: jinja
    - user: root

/etc/rc0.d/K01{{ pillar['web_daemon'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['web_daemon'] }}

/etc/rc1.d/K01{{ pillar['web_daemon'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['web_daemon'] }}

/etc/rc2.d/S01{{ pillar['web_daemon'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['web_daemon'] }}

/etc/rc3.d/S01{{ pillar['web_daemon'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['web_daemon'] }}

/etc/rc4.d/S01{{ pillar['web_daemon'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['web_daemon'] }}

/etc/rc5.d/S01{{ pillar['web_daemon'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['web_daemon'] }}

/etc/rc6.d/K01{{ pillar['web_daemon'] }}:
  file.symlink:
    - target: /etc/init.d/{{ pillar['web_daemon'] }}

/etc/init.d/{{ pillar['web_daemon'] }}:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://web/init.{{ pillar['web_daemon'] }}.jinja
    - template: jinja
    - user: root

{{ pillar['system_log_directory'] }}/{{ pillar['web_daemon'] }}:
  file.directory:
    - group: {{ pillar['web_daemon_username'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['web_daemon_username'] }}

{{ pillar['system_log_directory'] }}/{{ pillar['web_daemon'] }}/{{ pillar['web_daemon'] }}.log:
  file.managed:
    - group: {{ pillar['web_daemon_username'] }}
    - mode: 0644
    - replace: False
    - user: {{ pillar['web_daemon_username'] }}

{{ pillar['system_logrotate_conf_directory'] }}/{{ pillar['web_daemon'] }}:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://web/logrotate.{{ pillar['web_daemon'] }}.jinja
    - template: jinja
    - user: root

web-{{ pillar['web_daemon'] }}:
  service.running:
    - enable: True
    - name: {{ pillar['web_daemon'] }}
    - watch:
      - file: /etc/init.d/{{ pillar['web_daemon'] }}
