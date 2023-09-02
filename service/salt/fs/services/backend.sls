{% set cert_dir = pillar.cert_dir %}
{% set server_cert_key_file_name = pillar.server_cert_key_file_name %}

include:
  - base: package
  - base: services
  - base: web

{# Sanity check for inattentive administrators #}
{% if grains.get('server') == 'supervisor' or grains.get('server') == 'unified' %}

{% for packagename, package in pillar.get('npm-packages', {}).items() %}
{{ packagename }}-node-backend:
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
"{{ packagename }}-node-backend-package":
  npm.installed:
    - force_reinstall: True
{% elif package != None and 'version' in package %}
{% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
"{{ packagename }}@{{ package['version'] }}":
  npm.installed:
{% else %}
"{{ packagename }}":
  npm.installed:
{% endif %}
{% else %}
"{{ packagename }}":
  npm.installed:
{% endif %}
    - name: "{{ packagename }}"
    - require:
      - sls: package
{% endfor %}

/etc/nginx/conf.d/backend_api.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/backend/backend_api.conf.jinja
    - template: jinja
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

backend-www-node-directory:
  file.directory:
    - mode: 0755
    - name: {{ pillar.www_path }}/node
    - group: root
    - user: root

{{ pillar.www_path }}/node/restapi:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://service/node/restapi
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
      - file: /etc/nginx/conf.d/backend_api.conf

node-backend:
  service.running:
    - enable: True
    - name: node
    - watch:
      - file: {{ pillar.www_path }}/node
      - file: /etc/init.d/node
      - file: /etc/nginx/conf.d/backend_api.conf
    - require:
      - sls: web

# START equities application backend section

{% for datasource_name, datasource in pillar.get('equities_datasources', {}).items() %}

{{ datasource_name }}_remove:
  module.run:
    - mongo.remove_object:
      - database: equities
      - collection: datasources
      - query: { "DataSource": "{{ datasource_name }}" }

{{ datasource_name }}_insert:
  module.run:
    - mongo.insert_object:
      - database: equities
      - collection: datasources
      - object: { {% for key, value in datasource.items() %} "{{ key }}": "{{ value }}", {% endfor %} "DataSource": "{{ datasource_name }}" }

{% endfor %}

/usr/local/lib/python3.9/dist-packages/olympus/securities/equities/config/symbol_corrections.json.config:
  file.managed:
    - group: root
    - mode: 0644
    - source: salt://services/backend/symbol_corrections.json.jinja
    - template: jinja
    - user: root

/usr/local/lib/python3.9/dist-packages/olympus/securities/equities/config/symbol_watchlists.json.config:
  file.managed:
    - group: root
    - mode: 0644
    - source: salt://services/backend/symbol_watchlists.json.jinja
    - template: jinja
    - user: root

initialize_olympus_equities:
  cmd.run:
    - name: "su -s /bin/bash -c '/usr/local/bin/olympus/securities/equities/init_equities.py' {{ pillar['core-app-user'] }}"
    - user: root
    - require: 
      - node-backend

# Remove all symbol data stored in redis across all minions
regen_equities_symbols_redis:
  cmd.run:
    - name: salt '*' redis.delete_securities_equities_symbols
    - require: 
      - initialize_olympus_equities

{% endif %}
