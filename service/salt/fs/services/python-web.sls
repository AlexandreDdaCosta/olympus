include:
  - base: package
  - base: security

{% for packagename, package in pillar.get('python-web-service-packages', {}).items() %}
{{ packagename }}-python-web:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or 'version' not in package %}
  pkg.latest:
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
    - name: {{ packagename }}
{% if 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('python-web-service-pip-packages', {}).items() %}
{{ packagename }}:
  pip.installed:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - name: {{ packagename }}
    - upgrade: True
{% elif 'version' in package %}
    - name: {{ packagename }} {{ package['version'] }}
{% else %}
    - name: {{ packagename }}
{% endif %}
    - require:
      - sls: package
{% endfor %}

uwsgi-group:
  group.present:
    - name: uwsgi
    - system: True

uwsgi-user:
  user.present:
    - createhome: True
    - fullname: uWSGI
    - name: uwsgi
    - shell: /bin/false
    - home: /home/uwsgi
    - groups:
      - uwsgi

/etc/uwsgi/vassals:
    file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

/etc/uwsgi.ini:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/python-web/files/uwsgi.ini
    - user: root

/var/run/uwsgi.pid:
  file.managed:
    - group: uwsgi
    - mode: 0644
    - user: uwsgi

/etc/rc0.d/K01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc1.d/K01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc2.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc3.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc4.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc5.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc6.d/K01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/init.d/uwsgi:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/python-web/files/init.uwsgi
    - user: root

/etc/logrotate.d/uwsgi:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/python-web/files/logrotate.uwsgi
    - user: root

/var/log/uwsgi.log:
  file.managed:
    - group: uwsgi
    - mode: 0644
    - user: uwsgi

uwsgi-daemon:
  service.running:
    - enable: True
    - name: uwsgi
    - watch:
      - file: /etc/init.d/uwsgi
