{% set cert_dir = pillar.cert_dir %}
{% set cert_dir_client = pillar.cert_dir_client %}
{% set server_cert_file_name = pillar.server_cert_file_name %}
{% set server_cert_chained_file_name = pillar.server_cert_chained_file_name %}
{% set server_cert_combined_file_name = pillar.server_cert_combined_file_name %}
{% set server_cert_key_file_name = pillar.server_cert_key_file_name %}

include:
  - base: package

# BEGIN Server certificates and keys

{{ cert_dir }}:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{%- if grains.get('server') %}
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
    - name: 'openssl req -new -x509 -days 9999 -config {{ cert_dir }}/ca.cnf -keyout {{ cert_dir }}/ca-key.pem -out {{ cert_dir }}/ca-crt.pem'
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

{{ host }}_client-csr.pem_sign:
  cmd.run:
    - name: openssl x509 -req -extfile {{ dir }}/client.cnf -days 999 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in {{ dir }}/client-csr.pem -CA {{ cert_dir }}/ca-crt.pem -CAkey {{ cert_dir }}/ca-key.pem -CAcreateserial -out {{ dir }}/client-crt.pem

{{ host }}_client-crt-key.pem:
  cmd.run:
    - name: cat {{ dir }}/client-key.pem  {{ dir }}/client-crt.pem > {{ dir }}/client-crt-key.pem

{%- endfor %}

# Local certificates and chains

{{ server_cert_key_file_name }}:
  cmd.run:
    - name: 'openssl genrsa -out {{ cert_dir }}/{{ server_cert_key_file_name }} 4096'
    - require: 
      - {{ cert_dir }}/ca.cnf

server.cnf:
  file.managed:
    - group: root
    - mode: 600
    - name: {{ cert_dir }}/server.cnf
    - source: salt://security/server.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -config {{ cert_dir }}/server.cnf -key {{ cert_dir }}/{{ server_cert_key_file_name }} -out {{ cert_dir }}/server-csr.pem'
    - require: 
      - {{ server_cert_key_file_name }}

create_server_cert:
  cmd.run:
    - name: 'openssl x509 -req -extfile {{ cert_dir }}/server.cnf -days 365 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in {{ cert_dir }}/server-csr.pem -CA {{ cert_dir }}/ca-crt.pem -CAkey {{ cert_dir }}/ca-key.pem -CAcreateserial -out {{ cert_dir }}/{{ server_cert_file_name }}'
    - require: 
      - server.cnf

create_chained_cert:
  cmd.run:
    - name: cat {{ cert_dir }}/{{ server_cert_file_name }} {{ cert_dir }}/ca-crt.pem > {{ cert_dir }}/{{ server_cert_chained_file_name }}
    - require: 
      - create_server_cert

create_combined_cert:
  cmd.run:
    - name: cat {{ cert_dir }}/{{ server_cert_key_file_name }} {{ cert_dir }}/{{ server_cert_file_name }} > {{ cert_dir }}/{{ server_cert_combined_file_name }}
    - require: 
      - create_chained_cert

copy_CA_cert_local:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/ca-crt.pem.crt
    - source: {{ cert_dir }}/ca-crt.pem
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
    - name: salt '{{ grains.get('localhost') }}' cp.push {{ cert_dir }}/ca-crt.pem
    - require: 
      - trust_server_cert

# Trigger all minions to get supervisor CA certificate
get_client_cert_and_key:
  cmd.run:
    - name: salt '*' cp.get_file "salt://{{ grains.get('localhost') }}{{ cert_dir }}/ca-crt.pem" /usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt
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

# Trigger all minions to update combined client certificate/key file:
transfer_client_certficate_key_files:
  cmd.run:
    - name: salt '*' cp.get_file "salt://client_certificates/{% raw %}{{ grains.localhost }}{% endraw %}/client-crt-key.pem" {{ cert_dir }}/client-crt-key.pem template=jinja
    - require:
      - regen_trusted_CA

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

postgresql.{{ server_cert_key_file_name }}.perms:
  cmd.run:
    - name: 'if grep -q ssl-cert /etc/group; then chgrp ssl-cert {{ cert_dir }}/postgresql.{{ server_cert_key_file_name }}; fi;'
    - require: 
      - postgresql.{{ server_cert_key_file_name }}

postgresql.server.cnf:
  file.managed:
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
    - name: 'openssl x509 -req -extfile {{ cert_dir }}/postgresql.server.cnf -days 365 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in {{ cert_dir }}/postgresql.server-csr.pem -CA {{ cert_dir }}/ca-crt.pem -CAkey {{ cert_dir }}/ca-key.pem -CAcreateserial -out {{ cert_dir }}/postgresql.{{ server_cert_file_name }}'
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
{% endif %}

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

#random_root_password:
#  cmd.run:
#    - name: umask 0077; openssl rand -base64 21 > /root/passwd; cat /root/passwd | passwd root --stdin; rm -f /root/passwd
