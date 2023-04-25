{#
To redo security settings systemwide, run the following:

sudo -i salt '*' state.sls security -v

This will redo users (and associated SSH keys), stored passwords, and SSL certificates on all connected servers. Cookies will also be
invaidated and open sessions closed. 
#}

{% set cert_dir = pillar.cert_dir %}
{% set cert_dir_client = pillar.cert_dir_client %}
{% set server_cert_file_name = pillar.server_cert_file_name %}
{% set server_cert_authority_file_name = pillar.server_cert_authority_file_name %}
{% set server_cert_chained_file_name = pillar.server_cert_chained_file_name %}
{% set server_cert_combined_file_name = pillar.server_cert_combined_file_name %}
{% set server_cert_key_file_name = pillar.server_cert_key_file_name %}
{% set random_string_generator='echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(100)))" | /usr/bin/python3' %}
{% set check_mongo_certs_available="[ -f \'" + pillar.cert_dir + "/" + pillar.server_cert_combined_file_name + "\' ] && echo \'Yes\' | wc -l" %}
{% set check_redis_default_password="if [ -f /etc/redis/users.acl ]; then password=`grep default /etc/redis/users.acl | sed -e \'s/.*>//\'`; echo $password; else echo \'\'; fi;" %}
{% set old_redis_default_password = salt['cmd.shell'](check_redis_default_password) %}

include:
  - base: firewall
  - base: services
  - base: users

/etc/password:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0600
    - user: root

/etc/password/restapi:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0600
    - user: root

openssh-server-service:
  file.managed:
    - group: root
    - mode: 0600
    - name: /etc/ssh/sshd_config
    - source: salt://security/files/sshd_config
    - user: root
    - require:
      - pkg: openssh-server
  service.running:
    - enable: True
    - name: sshd
    - restart: True
    - watch:
        - file: /etc/ssh/sshd_config
        - pkg: openssh-server

systmctl_enable_user_sshagent
  cmd.run:
    - name: systemctl --user enable ssh-agent

fail2ban-service:
  service.running:
    - enable: True
    - name: fail2ban
    - restart: True
    - watch:
        - pkg: fail2ban

sudo-config:
  file.managed:
    - group: root
    - mode: 0440
    - name: /etc/sudoers.d/olympus
    - source: salt://security/files/sudoers.d/olympus
    - user: root

selinux.config:
  file.managed:
    - group: root
    - mode: 0644
    - name: /etc/selinux/config
    - source: salt://security/files/selinux/config
    - user: root

90-nproc.conf:
  file.managed:
    - group: root
    - mode: 0644
    - name: /etc/security/limits.d/90-nproc.conf
    - source: salt://security/files/90-nproc.conf
    - user: root

# BEGIN Server certificates and keys

{{ cert_dir }}:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{%- if grains.get('server') == 'unified' or grains.get('server') == 'supervisor' %}

{{ cert_dir_client }}:
  file.directory:
    - group: root
    - makedirs: True
    - mode: 0600
    - user: root

# Regenerate CA

{{ cert_dir }}/ca.cnf:
  file.managed:
    - context:
      ip_addresses: {{ grains.get('ipv4') }}
    - group: root
    - mode: 600
    - source: salt://security/ca.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -x509 -days 9999 -config {{ cert_dir }}/ca.cnf -keyout {{ cert_dir }}/ca-key.pem -out {{ cert_dir }}/{{ server_cert_authority_file_name }}'
    - onchanges:
      - file: {{ cert_dir }}/ca.cnf

# Create keys/csr/pem for minions, missing only

{%- for host, hostinfo in salt['mine.get']('*', 'grains.items').items() -%}
{% set dir = cert_dir_client + host %}

{{ dir }}:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0600
    - user: root

{{ host }}_client-key.pem:
  cmd:
    - run
    - name: 'openssl genrsa -out {{ dir }}/client-key.pem 4096'
    - unless: 'test -f {{ dir }}/client-key.pem && test -f {{ dir }}/client-csr.pem'

{{ host }}_client-key_perms:
  cmd:
    - run
    - name: 'chmod 0640 {{ dir }}/client-key.pem; chgrp clientcert {{ dir }}/client-key.pem'

{{ dir }}/client.cnf:
  file.managed:
    - context:
      client_hostname: {{ host }}
      ip_addresses: {{ hostinfo['ipv4'] }}
    - group: root
    - mode: 600
    - source: salt://security/client.cnf.jinja
    - template: jinja
    - user: root

{{ host }}_client-csr.pem:
  cmd.run:
    - onchanges:
      - file: {{ dir }}/client.cnf
    - name: 'openssl req -new -config {{ dir }}/client.cnf -key {{ dir }}/client-key.pem -out {{ dir }}/client-csr.pem'
    - name: 'openssl req -new -x509 -days 9999 -config {{ cert_dir }}/ca.cnf -keyout {{ cert_dir }}/ca-key.pem -out {{ cert_dir }}/{{ server_cert_authority_file_name }}'

{{ host }}_client-csr.pem_sign:
  cmd.run:
    - name: openssl x509 -req -extfile {{ dir }}/client.cnf -days 999 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in {{ dir }}/client-csr.pem -CA {{ cert_dir }}/{{ server_cert_authority_file_name }} -CAkey {{ cert_dir }}/ca-key.pem -CAcreateserial -out {{ dir }}/client-crt.pem

{{ host }}_client-key-crt.pem:
  cmd.run:
    - name: cat {{ dir }}/client-key.pem {{ dir }}/client-crt.pem > {{ dir }}/client-key-crt.pem

{{ host }}_client-key-crt_perms:
  cmd:
    - run
    - name: 'chmod 0640 {{ dir }}/client-key-crt.pem; chgrp clientcert {{ dir }}/client-key-crt.pem'

{%- endfor %}

# Local certificates and chains

{{ server_cert_key_file_name }}:
  cmd.run:
    - name: 'openssl genrsa -out {{ cert_dir }}/{{ server_cert_key_file_name }} 4096'
    - require: 
      - {{ cert_dir }}/ca.cnf

{{ server_cert_key_file_name }}_perms:
  cmd:
    - run
    - name: 'chmod 0640 {{ cert_dir }}/{{ server_cert_key_file_name }}; chgrp servercert {{ cert_dir }}/{{ server_cert_key_file_name }}'
    - require: 
      - {{ server_cert_key_file_name }}

server.cnf:
  file.managed:
    - context:
      ip_addresses: {{ grains.get('ipv4') }}
    - group: root
    - mode: 600
    - name: {{ cert_dir }}/server.cnf
    - source: salt://security/server.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -config {{ cert_dir }}/server.cnf -extensions v3_req -key {{ cert_dir }}/{{ server_cert_key_file_name }} -out {{ cert_dir }}/server-csr.pem'
    - require: 
      - {{ server_cert_key_file_name }}

create_server_cert:
  cmd.run:
    - name: 'openssl x509 -req -extfile {{ cert_dir }}/server.cnf -extensions v3_req -days 365 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in {{ cert_dir }}/server-csr.pem -CA {{ cert_dir }}/{{ server_cert_authority_file_name }} -CAkey {{ cert_dir }}/ca-key.pem -CAcreateserial -out {{ cert_dir }}/{{ server_cert_file_name }}'
    - require: 
      - server.cnf

create_chained_cert:
  cmd.run:
    - name: cat {{ cert_dir }}/{{ server_cert_file_name }} {{ cert_dir }}/{{ server_cert_authority_file_name }} > {{ cert_dir }}/{{ server_cert_chained_file_name }}
    - require: 
      - create_server_cert

create_combined_cert:
  cmd.run:
    - name: cat {{ cert_dir }}/{{ server_cert_key_file_name }} {{ cert_dir }}/{{ server_cert_file_name }} > {{ cert_dir }}/{{ server_cert_combined_file_name }}
    - require: 
      - create_chained_cert

create_combined_cert_perms:
  cmd:
    - run
    - name: 'chmod 0640 {{ cert_dir }}/{{ server_cert_combined_file_name }}; chgrp servercert {{ cert_dir }}/{{ server_cert_combined_file_name }}'
    - require: 
      - create_combined_cert

copy_CA_cert_local:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/{{ server_cert_authority_file_name }}.crt
    - source: {{ cert_dir }}/{{ server_cert_authority_file_name }}
    - user: root
    - require: 
      - create_combined_cert

trust_server_cert:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/{{ server_cert_file_name }}.crt
    - source: {{ cert_dir }}/{{ server_cert_file_name }}
    - user: root
    - require: 
      - copy_CA_cert_local

# Push CA cert from supervisor minion to master
push_CA_cert:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' cp.push {{ cert_dir }}/{{ server_cert_authority_file_name }}
    - require: 
      - trust_server_cert

# Trigger all minions to get supervisor CA certificate
get_client_cert_and_key:
  cmd.run:
    - name: salt '*' cp.get_file "salt://{{ grains.get('localhost') }}{{ cert_dir }}/{{ server_cert_authority_file_name }}" /usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt
    - require: 
      - push_CA_cert

# Trigger all minions to update trusted certificate store
regen_trusted_CA:
  cmd.run:
    - name: salt '*' cmd.run '/usr/sbin/update-ca-certificates --fresh'

# Trigger all minions to update client certificate:
transfer_client_certificates:
  cmd.run:
    - name: salt '*' cp.get_file "salt://client_certificates/{% raw %}{{ grains.localhost }}{% endraw %}/client-crt.pem" {{ cert_dir }}/client-crt.pem template=jinja
    - require:
      - regen_trusted_CA

# Trigger all minions to update client key:
transfer_client_keys:
  cmd.run:
    - name: salt '*' cp.get_file "salt://client_certificates/{% raw %}{{ grains.localhost }}{% endraw %}/client-key.pem" {{ cert_dir }}/client-key.pem template=jinja
    - require:
      - regen_trusted_CA

# Trigger all minions to set client key permissions:
set_client_key_permission:
  cmd.run:
    - name: salt '*' cmd.run 'chmod 0640 {{ cert_dir }}/client-key.pem; chgrp clientcert {{ cert_dir }}/client-key.pem'
    - require:
      - transfer_client_keys

# Trigger all minions to update combined client certificate/key file:
transfer_client_certficate_key_files:
  cmd.run:
    - name: salt '*' cp.get_file "salt://client_certificates/{% raw %}{{ grains.localhost }}{% endraw %}/client-key-crt.pem" {{ cert_dir }}/client-key-crt.pem template=jinja
    - require:
      - regen_trusted_CA

# Trigger all minions to set combined client certificate/key permissions:
set_client_certficate_key_file_permissions:
  cmd.run:
    - name: salt '*' cmd.run 'chmod 0640 {{ cert_dir }}/client-key-crt.pem; chgrp clientcert {{ cert_dir }}/client-key-crt.pem'
    - require:
      - transfer_client_certficate_key_files

# Trigger all minions to restart nginx, if running
cert_www_restart:
  cmd.run:
    - name: salt '*' cmd.run 'service nginx status; if [ $? = 0 ]; then service nginx restart; fi;'
    - require:
      - regen_trusted_CA

# START postgres section

postgresql.{{ server_cert_key_file_name }}:
  cmd.run:
    - name: 'openssl genrsa -out {{ cert_dir }}/postgresql.{{ server_cert_key_file_name }} 4096; chmod 0640 {{ cert_dir }}/postgresql.{{ server_cert_key_file_name }}'
    - require: 
      - {{ cert_dir }}/ca.cnf

postgresql.{{ server_cert_key_file_name }}_perms:
  cmd:
    - run
    - name: 'chmod 0640 {{ cert_dir }}/postgresql.{{ server_cert_key_file_name }}; chgrp pgcert {{ cert_dir }}/postgresql.{{ server_cert_key_file_name }}'

postgresql.server.cnf:
  file.managed:
    - context:
      ip_addresses: {{ grains.get('ipv4') }}
    - group: root
    - mode: 600
    - name: {{ cert_dir }}/postgresql.server.cnf
    - source: salt://security/server.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -config {{ cert_dir }}/postgresql.server.cnf -key {{ cert_dir }}/postgresql.{{ server_cert_key_file_name }} -out {{ cert_dir }}/postgresql.server-csr.pem'
    - require: 
      - postgresql.{{ server_cert_key_file_name }}

create_postgresql_server_cert:
  cmd.run:
    - name: 'openssl x509 -req -extfile {{ cert_dir }}/postgresql.server.cnf -days 365 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in {{ cert_dir }}/postgresql.server-csr.pem -CA {{ cert_dir }}/{{ server_cert_authority_file_name }} -CAkey {{ cert_dir }}/ca-key.pem -CAcreateserial -out {{ cert_dir }}/postgresql.{{ server_cert_file_name }}'
    - require: 
      - postgresql.server.cnf

cert_postgresql_restart:
  cmd.run:
    - name: service postgresql status; if [ $? = 0 ]; then service postgresql restart; fi;
    - require:
      - regen_trusted_CA

# END postgres section

cert_mongo_restart:
  cmd.run:
    - name: service mongod status; if [ $? = 0 ]; then service mongod restart; fi;
    - require:
      - regen_trusted_CA

# END Server certificates and keys

# BEGIN Shared credentials

# 1. Update database credential in minion data
update_minion_credential_data:
  cmd.run:
    - name: salt -C 'G@services:frontend or G@services:backend' data.update frontend_db_key {{ pillar['random_key']['frontend_db_key'] }}

# 2. Call credentials update script for all frontend/backend minions
update_db_credential:
  cmd.run:
    - name: salt -C 'G@services:frontend or G@services:backend' credentials.shared_database
    - require: 
      - update_minion_credential_data

# END Shared credentials

{% endif %}

# Mongo access passwords, database permissions, and password files 

{% for username, user in pillar.get('users', {}).items() %}
{% if 'server' not in user or grains.get('server') in user['server'] -%}
{% if 'is_staff' in user and user['is_staff'] -%}

{{ username }}_mongodb_staff:
  module.run:
    - mongo.user:
      - username: {{ username }}
      - password: {{ salt['cmd.shell'](random_string_generator) }}
      - admin: True

{% elif 'mongodb' in user -%}
{% if 'admin' in user['mongodb'] and user['mongodb']['admin'] -%}

{{ username }}_mongodb_admin:
  module.run:
    - mongo.user:
      - username: {{ username }}
      - password: {{ salt['cmd.shell'](random_string_generator) }}
      - admin: True

{% else -%}

{{ username }}_mongodb_user:
  module.run:
    - mongo.user:
      - username: {{ username }}
      - password: {{ salt['cmd.shell'](random_string_generator) }}
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
    - source: salt://services/mongod.conf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: service mongod restart

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

{% if grains.get('server') == 'unified' or grains.get('server') == 'supervisor' %}
{% for username, user in pillar.get('users', {}).items() %}
{% if 'restapi' in user %}

# Write restapi password to local password file
{{ username }}_restapi_password_file:
  file.managed:
    - context:
      secret: {{ user['restapi']['password'] }}
    - group: root
    - makedirs: False
    - name: /etc/password/restapi/{{ username }}
    - mode: 0600
    - source: salt://security/secret.jinja
    - template: jinja
    - user: root

copy_{{ username }}_restapi_password_file:
  cmd.run:
    - name: salt-cp -C 'G@server:database or G@server:interface or G@server:worker' /etc/password/restapi/{{ username }} /etc/password/restapi/{{ username }}
    - require: 
      - {{ username }}_restapi_password_file

# Call minions to rotate restapi password file (remote module will check if user exists on server)
rotate_{{ username }}_restapi_password_file:
  cmd.run:
    - name: salt '*' credentials.rotate_restapi_password_file {{ username }} /etc/password/restapi/{{ username }}
    - require: 
      - copy_{{ username }}_restapi_password_file

# Update user authorization entry in backend mongodb
# NOTE: No defined routes implies all available routes, all available verbs

{{ username }}_restapi_user:
  module.run:
    - mongo.insert_update_restapi_user:
      - username: {{ username }}
      - password: {{ user['restapi']['password'] }}
{%- if 'routes' in user['restapi'] %}
      - defined_routes: {{ user['restapi']['routes'] }}
{%- endif %}
    - require: 
      - rotate_{{ username }}_restapi_password_file

{% endif %}
{% endfor %}

# Create/update restapi secret file. The secret is used to sign and validate all tokens issued by the API.

restapi_access_token_secret:
  file.managed:
    - context:
      secret: {{ salt['cmd.shell'](random_string_generator) }}
    - group: {{ pillar['backend-user'] }}  
    - makedirs: False
    - name: /home/{{ pillar['backend-user'] }}/etc/access_token_secret
    - mode: 0600
    - source: salt://security/secret.jinja
    - template: jinja
    - user: {{ pillar['backend-user'] }}

restapi_refresh_token_secret:
  file.managed:
    - context:
      secret: {{ salt['cmd.shell'](random_string_generator) }}
    - group: {{ pillar['backend-user'] }}  
    - makedirs: False
    - name: /home/{{ pillar['backend-user'] }}/etc/refresh_token_secret
    - mode: 0600
    - require:
      - restapi_access_token_secret
    - source: salt://security/secret.jinja
    - template: jinja
    - user: {{ pillar['backend-user'] }}  

{% endif %}

security_node_restart:
  cmd.run:
    - name: service node status; if [ $? = 0 ]; then service node restart; fi;

# Access control for redis server

redis_acl_list:
  file.managed:
    - group: redis
    - makedirs: False
    - mode: 0640
    - name: /etc/redis/users.acl
    - source: salt://security/redis/users.acl.jinja
    - template: jinja
    - user: redis

# Write redis password to local password file
{% for username, user in pillar.get('users', {}).items() -%}
{% if 'server' not in user or grains.get('server') in user['server'] -%}
{% if 'redis' in user -%}

{{ username }}_redis_password_file:
  file.managed:
    - context:
      secret: {{ user['redis']['password'] }}
    - group: {{ username }}
    - makedirs: False
    - name: /home/{{ username }}/etc/redis_password
    - mode: 0600
    - source: salt://security/secret.jinja
    - template: jinja
    - user: {{ username }}

{% endif -%}
{% endif -%}
{%- endfor -%}

/usr/local/bin/load_redis_acl.sh:
  file.managed:
    - group: root
    - mode: 0700
    - source: salt://security/files/load_redis_acl.sh
    - user: root

redis_acl_reload:
  cmd.run:
    - name: env REDIS_DEFAULT_PASSWORD={{ old_redis_default_password }} /usr/local/bin/load_redis_acl.sh
    - require:
      - redis_acl_list

#random_root_password:
#  cmd.run:
#    - name: umask 0077; openssl rand -base64 21 > /root/passwd; cat /root/passwd | passwd root --stdin; rm -f /root/passwd
