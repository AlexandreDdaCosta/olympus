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

/etc/postgresql/9.6/main/pg_hba.conf:
  file.managed:
    - group: postgres
    - mode: 0640
    - source: salt://services/backend/files/pg_hba.conf
    - user: postgres

/etc/postgresql/9.6/main/postgresql.conf:
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
      - file: /etc/postgresql/9.6/main/postgresql.conf
      - pkg: pgadmin3
      - pkg: postgresql-9.6
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

{% set new_password = salt['data.get']('frontend_db_key', None) %}
{% if new_password is not none %}
frontend_db_user_pwd_reset:
  cmd.run:
    - name: sudo -u postgres psql -c "ALTER USER {{ pillar['frontend-user'] }} ENCRYPTED PASSWORD '{{ new_password }}';"

# Clear frontend_db_key from data store if no frontend service on this server
{% if 'frontend' not in grains.get('services') %}
delete_password_data:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' data.pop frontend_db_key
    - require: 
      - frontend_db_user_pwd_reset
{% endif %}
{% endif %}

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
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://service/node
    - user: root

{{ pillar.www_path }}/node/restapi/package.json:
  file.managed:
    - group: root
    - mode: 0755
    - user: root
    - source: salt://services/backend/package.json.jinja
    - template: jinja

nginx-backend:
  service.running:
    - name: nginx
    - watch:
      - file: /etc/nginx/conf.d/node.conf

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
