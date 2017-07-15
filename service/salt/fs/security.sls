{% set client_certificates = '/etc/ssl/salt/client_certificates/' %}

include:
  - base: package

/etc/ssl/localcerts:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{%- if grains.get('server') and grains.get('server') == 'supervisor' %}

{{ client_certificates }}:
  file.directory:
    - group: root
    - makedirs: True
    - mode: 0600
    - user: root

# Regenerate CA

/etc/ssl/localcerts/ca.cnf:
  file.managed:
    - group: root
    - mode: 600
    - source: salt://security/ca.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -x509 -days 9999 -config /etc/ssl/localcerts/ca.cnf -keyout /etc/ssl/localcerts/ca-key.pem -out /etc/ssl/localcerts/ca-crt.pem'
    - onchanges:
      - file: /etc/ssl/localcerts/ca.cnf

# Create keys/csr/pem for minions, missing only

{%- for host, hostinfo in salt['mine.get']('*', 'grains.items').items() -%}
{% set dir = client_certificates + host %}

{{ dir }}:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0600
    - user: root

{{ host }}_client-key.pem:
  cmd:
    - run
    - name: 'openssl genrsa -out {{ client_certificates }}{{ host }}/client-key.pem 4096'
    - unless: 'test -f {{ client_certificates }}{{ host }}/client-key.pem && test -f {{ client_certificates }}{{ host }}/client-csr.pem'

{{ client_certificates }}{{ host }}/client.cnf:
  file.managed:
    - context:
      client_hostname: {{ host }}
    - group: root
    - mode: 600
    - source: salt://security/client.cnf.jinja
    - template: jinja
    - user: root

{{ host }}_client-csr.pem:
  cmd.run:
    - onchanges:
      - file: {{ client_certificates }}{{ host }}/client.cnf
    - name: 'openssl req -new -config {{ client_certificates }}{{ host }}/client.cnf -key {{ client_certificates }}{{ host }}/client-key.pem -out {{ client_certificates }}{{ host }}/client-csr.pem'

{{ host }}_client-csr.pem_sign:
  cmd.run:
    - name: openssl x509 -req -extfile {{ client_certificates }}{{ host }}/client.cnf -days 999 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in {{ client_certificates }}{{ host }}/client-csr.pem -CA /etc/ssl/localcerts/ca-crt.pem -CAkey /etc/ssl/localcerts/ca-key.pem -CAcreateserial -out {{ client_certificates }}{{ host }}/client-crt.pem

{%- endfor %}

# Local certificates and chains

server-key.pem:
  cmd.run:
    - name: 'openssl genrsa -out /etc/ssl/localcerts/server-key.pem 4096'
    - require: 
      - /etc/ssl/localcerts/ca.cnf

server.cnf:
  file.managed:
    - group: root
    - mode: 600
    - name: /etc/ssl/localcerts/server.cnf
    - source: salt://security/server.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -config /etc/ssl/localcerts/server.cnf -key /etc/ssl/localcerts/server-key.pem -out /etc/ssl/localcerts/server-csr.pem'
    - require: 
      - server-key.pem

create_server_cert:
  cmd.run:
    - name: 'openssl x509 -req -extfile /etc/ssl/localcerts/server.cnf -days 365 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in /etc/ssl/localcerts/server-csr.pem -CA /etc/ssl/localcerts/ca-crt.pem -CAkey /etc/ssl/localcerts/ca-key.pem -CAcreateserial -out /etc/ssl/localcerts/server-crt.pem'
    - require: 
      - server.cnf

create_chained_cert:
  cmd.run:
    - name: cat /etc/ssl/localcerts/server-crt.pem /etc/ssl/localcerts/ca-crt.pem > /etc/ssl/localcerts/server-crt-chain.pem
    - require: 
      - create_server_cert

copy_CA_cert_local:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/ca-crt.pem.crt
    - source: /etc/ssl/localcerts/ca-crt.pem
    - user: root
    - require: 
      - create_chained_cert

trust_server_cert:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/server-crt.pem.crt
    - source: /etc/ssl/localcerts/server-crt.pem
    - user: root
    - require: 
      - copy_CA_cert_local

# Push CA cert from supervisor minion to master
push_CA_cert:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' cp.push /etc/ssl/localcerts/ca-crt.pem
    - require: 
      - trust_server_cert

# Trigger all minions to get supervisor CA certificate
get_client_cert_and_key:
  cmd.run:
    - name: salt '*' cp.get_dir "salt://{{ grains.get('localhost') }}/etc/ssl/localcerts" /etc/ssl/localcerts
    - require: 
      - push_CA_cert

# Trigger all minions to copy regenerated supervisor CA cert 
copy_CA_cert:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/ca-crt-supervisor.pem.crt
    - source: /etc/ssl/localcerts/ca-crt.pem
    - user: root
    - require: 
      - get_client_cert_and_key

# Trigger all minions to update trusted certificate store
regen_trusted_CA:
  cmd.run:
    - name: salt '*' cmd.run '/usr/sbin/update-ca-certificates --fresh'

# Trigger all minions to update client certificate:
transfer_client_certificates:
  cmd.run:
    - name: salt '*' cp.get_file "salt://client_certificates/{% raw %}{{ grains.localhost }}{% endraw %}/client-crt.pem" /etc/ssl/localcerts/client-crt.pem template=jinja

# Trigger all minions to update client key:
transfer_client_keys:
  cmd.run:
    - name: salt '*' cp.get_file "salt://client_certificates/{% raw %}{{ grains.localhost }}{% endraw %}/client-key.pem" /etc/ssl/localcerts/client-key.pem template=jinja

cert_security_restart:
  cmd.run:
    - name: service nginx status; if [ $? = 0 ]; then service nginx restart; fi;
    - require:
      - regen_trusted_CA
      - transfer_client_certificates

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
