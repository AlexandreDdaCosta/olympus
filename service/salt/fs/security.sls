include:
  - base: package

/etc/ssl/localcerts:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0600
    - user: root

ca.cnf:
  file.managed:
    - group: root
    - mode: 600
    - name: /etc/ssl/localcerts/ca.cnf
    - source: salt://services/web/ca.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -x509 -days 9999 -config /etc/ssl/localcerts/ca.cnf -keyout /etc/ssl/localcerts/ca-key.pem -out /etc/ssl/localcerts/ca-crt.pem'

server-key.pem:
  cmd.run:
    - name: 'openssl genrsa -out /etc/ssl/localcerts/server-key.pem 4096'
    - require: 
      - ca.cnf

server.cnf:
  file.managed:
    - group: root
    - mode: 600
    - name: /etc/ssl/localcerts/server.cnf
    - source: salt://services/web/server.cnf.jinja
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

copy_CA_cert_local:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/ca-crt.pem.crt
    - source: /etc/ssl/localcerts/ca-crt.pem
    - user: root
    - require: 
      - create_server_cert

trust_server_cert:
  file.copy:
    - force: True
    - group: root
    - mode: 644
    - name: /usr/local/share/ca-certificates/server-crt.pem.crt
    - source: /etc/ssl/localcerts/server-crt.pem
    - user: root
  cmd.run:
    - name: /usr/sbin/update-ca-certificates --fresh 
    - require: 
      - copy_CA_cert_local

web_security_restart:
  cmd.run:
    - name: service nginx status; if [ $? = 0 ]; then service nginx restart; fi;
    - require:
      - trust_server_cert

{%- if grains.get('server') and grains.get('server') == 'supervisor' %}

# Push CA cert from minion to master
push_CA_cert:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' cp.push /etc/ssl/localcerts/ca-crt.pem
    - require: 
      - create_server_cert

# Trigger all minions to retrieve master CA cert 

copy_CA_cert:
  cmd.run:
    - name: salt '*' cp.get_file salt://{{ grains.get('localhost') }}/etc/ssl/localcerts/ca-crt.pem /usr/local/share/ca-certificates/ca-crt.pem.crt
    - require: 
      - push-CA-cert

# Trigger all minions to update certificate store

regen_trusted_CA:
  cmd.run:
    - name: salt '*' cmd.run '/usr/sbin/update-ca-certificates --fresh'
    - require: 
      - copy-CA-cert

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
