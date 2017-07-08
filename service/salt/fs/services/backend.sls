{% set api_path=pillar.www_path+'/node' %}

include:
  - base: package
  - base: services/web

{% for packagename, package in pillar.get('backend-packages', {}).items() %}
{{ packagename }}-nodejs-web:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or package != None and 'version' not in package %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if package != None and 'version' in package %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
    - name: {{ packagename }}
{% if package != None and 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('backend-npm-packages', {}).items() %}
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
{{ packagename }}:
    npm.installed:
      - force_reinstall: True
{% elif package != None and 'version' in package %}
{{ packagename }}@{{ package['version'] }}:
    npm.installed:
{% else %}
{{ packagename }}:
    npm.installed:
{% endif %}
      - require:
        - sls: package
{% endfor %}

/etc/postgresql/9.6/main/pg_hba.conf:
  file.managed:
    - group: postgres
    - mode: 0640
    - source: salt://services/backend/files/pg_hba.conf
    - user: postgres

/usr/lib/tmpfiles.d/postgresql.conf:
  file.managed:
    - group: postgres
    - mode: 0600
    - source: salt://services/backend/files/postgresql.conf
    - user: postgres

postgresql:
  service.running:
    - enable: True
    - watch:
      - file: /etc/postgresql/9.6/main/pg_hba.conf
      - file: /usr/lib/tmpfiles.d/postgresql.conf
      - pkg: pgadmin3
      - pkg: postgresql-9.6
    - require:
      - sls: services/web

backend-group:
  group.present:
    - name: {{ pillar['backend-user'] }}
    - system: True

backend-user:
  user.present:
    - createhome: True
    - fullname: {{ pillar['backend-user'] }}
    - name: {{ pillar['backend-user'] }}
    - shell: /bin/false
    - home: /home/{{ pillar['backend-user'] }}
    - groups:
      - {{ pillar['backend-user'] }}

/etc/mongod.conf:
  file.exists:
    - name: /etc/mongod.conf


/etc/nginx/conf.d/node.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/backend/files/node.conf
    - user: root

/etc/rc0.d/K01node:
  file.symlink:
    - target: /etc/init.d/node

/etc/rc1.d/K01node:
  file.symlink:
    - target: /etc/init.d/node

/etc/rc2.d/S01node:
  file.symlink:
    - target: /etc/init.d/node

/etc/rc3.d/S01node:
  file.symlink:
    - target: /etc/init.d/node

/etc/rc4.d/S01node:
  file.symlink:
    - target: /etc/init.d/node

/etc/rc5.d/S01node:
  file.symlink:
    - target: /etc/init.d/node

/etc/rc6.d/K01node:
  file.symlink:
    - target: /etc/init.d/node

/etc/init.d/node:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/backend/files/init.node
    - user: root

/etc/logrotate.d/node:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/backend/files/logrotate.node
    - user: root

/var/log/node:
  file.directory:
    - group: {{ pillar['backend-user'] }}
    - mode: 0755
    - user: {{ pillar['backend-user'] }}

{{ pillar.www_path }}/node:
  file.recurse:
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://service/node
    - user: root

nginx-backend:
  service.running:
    - name: nginx
    - watch:
      - file: /etc/nginx/conf.d/node.conf

mongod-backend:
  service.running:
    - name: mongod
    - watch:
      - file: /etc/mongod.conf

node-backend:
  service.running:
    - enable: True
    - name: node
    - watch:
      - file: {{ pillar.www_path }}/node
      - file: /etc/init.d/node
      - file: /etc/nginx/conf.d/node.conf
    - require:
      - sls: services/web
