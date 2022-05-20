{% set check_mongo_auth_enabled="/usr/bin/touch /etc/mongod.conf && grep '^[ ]*authorization: enabled' /etc/mongod.conf | wc -l" %}
{% set check_mongo_certs_available="[ -f \'" + pillar.cert_dir + "/" + pillar.server_cert_combined_file_name + "\' ] && echo \'Yes\' | wc -l" %}
{% set random_password_generator='echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(100)))" | /usr/bin/python3' %}

include:
  - base: package
  - base: users

atd:
  service.running:
    - enable: True
    - watch:
        - pkg: at

ntp-service:
  service.running:
    - enable: True
    - name: ntp
    - watch:
        - pkg: ntp

ntpd-timecheck:
  cmd.run:
    - name: service ntp stop; /usr/sbin/ntpdate pool.ntp.org; service ntp start

locate-updatedb:
  cmd.run:
    - name: updatedb

{%- if salt['cmd.shell'](check_mongo_auth_enabled) == 0 %}
/etc/mongod.conf:
  file.managed:
    - context:
      auth_enabled: false
      certs_available: false
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/files/mongod.conf.jinja
    - template: jinja
    - user: root
{%- endif %}

{#
Command line: 

Pre authentication enabled:

Without TLS: mongo
With TLS: mongo --tls --tlsCAFile /etc/ssl/localcerts/ca-crt.pem --tlsCertificateKeyFile /etc/ssl/localcerts/server-key-crt.pem --tlsAllowInvalidHostnames
(Assumes the certs exist, which only occurs after running security.sls, so not immediately upon server creation.
Also assumes your user has access to view the combined cert/key file via group membership.)

Post authentication enabled:

mongo --username `whoami` --password `cat /home/\`whoami\`/etc/mongodb_password` <TLS options as above for TLS>

Note that mongod only listens on localhost (127.0.0.1)
#}

systmctl_enable_mongod:
  cmd.run:
    - name: systemctl enable mongod

mongodb_proper_perms:
  cmd.run:
    - name: chown -R mongodb:mongodb /var/lib/mongodb
# Bug: Found bad perms of unknown origin

mongod-service:
  service.running:
    - enable: True
    - name: mongod
    - watch:
      - file: /etc/mongod.conf

# Mongo access passwords, database permissions, and password files 

{% for username, user in pillar.get('users', {}).items() %}
{% if 'server' not in user or grains.get('server') in user['server'] -%}
{% if 'is_staff' in user and user['is_staff'] -%}

{{ username }}_mongodb_staff:
  module.run:
    - mongo.user:
      - username: {{ username }}
      - password: {{ salt['cmd.shell'](random_password_generator) }}
      - admin: True

{% elif 'mongodb' in user -%}
{% if 'admin' in user['mongodb'] and user['mongodb']['admin'] -%}

{{ username }}_mongodb_admin:
  module.run:
    - mongo.user:
      - username: {{ username }}
      - password: {{ salt['cmd.shell'](random_password_generator) }}
      - admin: True

{% else -%}

{{ username }}_mongodb_user:
  module.run:
    - mongo.user:
      - username: {{ username }}
      - password: {{ salt['cmd.shell'](random_password_generator) }}
      - admin: False
{% if 'roles' in user['mongodb'] %}
      - roles: {{ user['mongodb']['roles'] }}
{% endif -%}

{% endif -%}
{% endif -%}
{% endif -%}
{% endfor %}

# With permissions in place, require authorization for mongodb

mongodb_set_authorization:
  file.managed:
    - context:
      auth_enabled: true
      cmd_result: {{ salt['cmd.shell'](check_mongo_certs_available) }}
{%- if salt['cmd.shell'](check_mongo_certs_available) == '1' %}
      certs_available: true
{%- else %}
      certs_available: false
{%- endif %}
    - group: root
    - makedirs: False
    - mode: 0644
    - name: /etc/mongod.conf
    - require: 
      - mongodb_mongodb_admin
    - source: salt://services/files/mongod.conf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: service mongod restart; service node status; if [ $? = 0 ]; then service node restart; fi;

{% set mongodb_users = [] %}
{% for username, user in pillar.get('users', {}).items() %}
{% if 'is_staff' in user and user['is_staff'] -%}
{% set mongodb_users = mongodb_users.append(username) %}
{% elif 'mongodb' in user -%}
{% set mongodb_users = mongodb_users.append(username) %}
{% endif %}
{% endfor %}

mongodb_purge_invalid_users:
  module.run:
    - mongo.purge_users:
      - valid_users: {{ mongodb_users }}

# Recognized user passwords for REST API

{% if grains.get('server') == 'unified' or grains.get('server') == 'supervisor' -%}
{% for username, user in pillar.get('users', {}).items() -%}

{% if 'is_staff' in user and user['is_staff'] -%}

# Call minions to rotate restapi password file (remote module will check if user exists on server)

# ALEX TODO

# Update password in mongodb

{{ username }}_restapi_staff:
  module.run:
    - mongo.insert_update_restapi_user:
      - username: {{ username }}
      - password: {{ user['restapi']['password'] }}
      - routes: []
      - all_routes: True

{% elif 'restapi' in user %}
{% if 'routes' in user['restapi'] %}
{% set restapi_routes=user['restapi']['routes'] %}
{% else %}
{% set restapi_routes=[] %}
{% endif %}

# Call minions to rotate restapi password file

# ALEX TODO

# Update password in mongodb

{{ username }}_restapi_user:
  module.run:
    - mongo.insert_update_restapi_user:
      - username: {{ username }}
      - password: {{ user['restapi']['password'] }}
      - routes: {{ restapi_routes }}
      - all_routes: False

{% endif %}
{% endfor %}
{% endif %}

{#
# ALEX
  node:
    restapi:
      password: {{ salt['cmd.shell'](random_password_generator) }}
      routes:
        - equities
    server:
      - supervisor
      - unified
#}
