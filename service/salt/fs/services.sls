include:
  - base: package

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

/etc/mongod.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/files/mongod.conf
    - user: root
{#
command line: 
With TLS: mongo --tls --tlsCAFile /etc/ssl/localcerts/ca-crt.pem --tlsCertificateKeyFile /etc/ssl/localcerts/server-key-crt.pem
(Assuming your user has access to view the combined cert/key file via group membership)
Without TLS: mongo
Note that mongod only listens on localhost (127.0.0.1)
#}

systmctl_enable_mongod:
  cmd.run:
    - name: systemctl enable mongod

mongodb_proper_perms:
  cmd.run:
    - name: chown -R mongodb:mongodb /var/lib/mongodb
{# Bug: Found bad perms of unknown origin #}

mongod-service:
  service.running:
    - enable: True
    - name: mongod
    - watch:
      - file: /etc/mongod.conf
