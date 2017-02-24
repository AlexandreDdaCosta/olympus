include:
  - base: repository
  - base: package
  - base: security

{% for packagename, package in pillar.get('web-service-packages', {}).items() %}
{{ packagename }}-web:
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
      - sls: repository
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('web-service-pip-packages', {}).items() %}
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
      - sls: repository
      - sls: package
{% endfor %}

web_certs:
  cmd:
    - run
    - name: 'openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -out /etc/ssl/localcerts/server.crt -keyout /etc/ssl/localcerts/server.key -subj "/C=US/ST=Lake Worth/L=Lake Worth/O=FeralCanids/OU=Olympus web services/CN=feralcanids.com"'
{% if pillar.refresh_security is not defined or not pillar.refresh_security %}
    - unless: 'test -f /etc/ssl/localcerts/server.crt && openssl verify /etc/ssl/localcerts/server.crt'
{% endif %}

nginx:
  service.running:
    - watch:
      - file: /etc/nginx/conf.d/default.conf
  file.managed:
    - name: /etc/nginx/conf.d/default.conf
    - source: salt://services/web/files/default.conf

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

/etc/uwsgi.ini
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/web/files/uwsgi.ini
    - user: root

/var/run/uwsgi.pid
  file.managed:
    - group: uwsgi
    - mode: 0644
    - user: uwsgi

/etc/init.d/uwsgi:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/web/files/init.uwsgi
    - user: root

/etc/logrotate.d/uwsgi:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/web/files/logrotate.uwsgi
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
