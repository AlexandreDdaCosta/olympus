{% set check_mongo_auth_enabled="/usr/bin/touch /etc/mongod.conf && grep '^[ ]*authorization: enabled' /etc/mongod.conf | wc -l" %}

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
    - source: salt://services/mongod.conf.jinja
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
{%- if salt['cmd.shell'](check_mongo_auth_enabled) == 0 %}
    - watch:
      - file: /etc/mongod.conf
{% endif %}

verify_redis_acl_file:
  cmd.run:
    - name: touch /etc/redis/users.acl

/etc/redis/redis.conf:
  file.managed:
    - group: redis
    - makedirs: False
    - mode: 0640
    - require:
      - verify_redis_acl_file
    - source: salt://services/files/redis.conf
    - user: redis

redis-service:
  service.running:
    - enable: True
    - name: redis
    - watch:
      - file: /etc/redis/redis.conf

