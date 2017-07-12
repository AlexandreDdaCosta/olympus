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
      - security: ca.cnf

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

local_certs:
  cmd:
    - run
    - name: 'openssl x509 -req -extfile /etc/ssl/localcerts/server.cnf -days 365 -passin "pass:{{ pillar['random_key']['ca_key'] }}" -in /etc/ssl/localcerts/server-csr.pem -CA /etc/ssl/localcerts/ca-crt.pem -CAkey /etc/ssl/localcerts/ca-key.pem -CAcreateserial -out /etc/ssl/localcerts/server-crt.pem'

{% if 'server' in hostinfo and hostinfo['server'] == 'supervisor' %}
# Push CA cert from minion to master
push-CA-cert:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' cp.push /etc/ssl/localcerts/ca-crt.pem
# Trigger all minions to retrieve file
# Trigger all minions to update certificate store
#    - name: /etc/ssl/localcerts/ca-crt.pem
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
