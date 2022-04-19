{% set api_path=pillar.www_path+'/node' %}
{% set cert_dir = pillar.cert_dir %}
{% set server_cert_key_file_name = pillar.server_cert_key_file_name %}

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
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
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
{% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
{{ packagename }}@{{ package['version'] }}:
    npm.installed:
{% else %}
{{ packagename }}:
    npm.installed:
{% endif %}
{% else %}
{{ packagename }}:
    npm.installed:
{% endif %}
      - require:
        - sls: package
{% endfor %}

/etc/postgresql/14/main/pg_hba.conf:
  file.managed:
    - group: postgres
    - mode: 0640
    - source: salt://services/backend/files/pg_hba.conf
    - user: postgres

/etc/postgresql/14/main/postgresql.conf:
  file.managed:
    - group: postgres
    - mode: 0600
    - source: salt://services/backend/postgresql.conf.jinja
    - template: jinja
    - user: postgres
  cmd.run:
    - name: chgrp ssl-cert {{ cert_dir }}/postgresql.{{ server_cert_key_file_name }}

postgresql:
  service.running:
    - enable: True
    - watch:
      - file: /etc/postgresql/14/main/pg_hba.conf
      - file: /etc/postgresql/14/main/postgresql.conf
      - pkg: pgadmin3
      - pkg: postgresql-14
    - require:
      - sls: services/web

olympus.db:
  postgres_database.present:
    - name: olympus

frontend_app_data.db:
  postgres_database.present:
    - name: app_data

frontend-user_data.db:
  postgres_database.present:
    - name: user_data

frontend_db_user:
  postgres_user.present:
    - default_password: 'md5{MD5OF({{ pillar['random_key']['frontend_db_key'] }})}'
    - encrypted: True
    - name: {{ pillar['frontend-user'] }}

frontend_db_user_pwd_reset:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' credentials.backend
    - require: 
      - frontend_db_user

frontend_app_data_privs:
  postgres_privileges.present:
    - name: {{ pillar['frontend-user'] }}
    - object_name: app_data
    - object_type: database
    - privileges:
      - ALL

frontend-user_data_privs:
  postgres_privileges.present:
    - name: {{ pillar['frontend-user'] }}
    - object_name: user_data
    - object_type: database
    - privileges:
      - ALL

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
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/backend/files/mongod.conf
    - user: root
{#
command line: 
mongo --tls --tlsCAFile /etc/ssl/localcerts/ca-crt.pem --tlsCertificateKeyFile /etc/ssl/localcerts/server-key-crt.pem --tlsAllowInvalidHostnames
#}

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
    - mode: 0644
    - source: salt://services/backend/files/logrotate.node
    - user: root

/var/log/node:
  file.directory:
    - group: {{ pillar['backend-user'] }}
    - mode: 0755
    - user: {{ pillar['backend-user'] }}

{{ pillar.www_path }}/node:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://service/node
    - user: root

{{ pillar.www_path }}/node/restapi/package.json:
  file.managed:
    - group: root
    - mode: 0644
    - user: root
    - source: salt://services/backend/package.json.jinja
    - template: jinja

nginx-backend:
  service.running:
    - name: nginx
    - watch:
      - file: /etc/nginx/conf.d/node.conf

systmctl_enable_mongod:
  cmd.run:
    - name: systemctl enable mongod

mongodb_proper_perms:
  cmd.run:
    - name: chown -R mongodb:mongodb /var/lib/mongodb
{# Bug: Found bad perms of unknown origin #}

mongod-backend:
  service.running:
    - enable: True
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

# START equities project backend section

initialize_olympus_equities:
  cmd.run:
    - name: "su -s /bin/bash -c '/usr/local/bin/olympus/init_equities.py --graceful' {{ pillar['core-app-user'] }}"
    - user: root
    - require: 
      - mongod-backend
      - node-backend

{% for datasource_name, datasource in pillar.get('equities_credentials', {}).items() %}
{{ datasource_name }}_delete:
  module.run:
    - name: mongodb.remove
    - collection: credentials
    - database: equities_us
    - port: 27017
    - query: '[{ "DataSource": {{ datasource_name }} }]'
    - require: 
      - initialize_olympus_equities

{{ datasource_name }}_insert:
  module.run:
    - name: mongodb.insert
    - collection: credentials
    - database: equities_us
    - objects: '[{ "DataSource": {{ datasource_name }}, "KeyName": {{ datasource['KeyName'] }}, "Key": {{ datasource['Key'] }}, "IssueEpochDate": {{datasource['IssueEpochDate'] }} }]'
    - port: 27017
    - require: 
      - initialize_olympus_equities

{% endfor %}
