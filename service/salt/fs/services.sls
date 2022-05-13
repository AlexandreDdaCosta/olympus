{%- set check_mongo_auth_enabled="/usr/bin/touch /etc/mongod.conf && grep '^[ ]*authorization: enabled' /etc/mongod.conf | wc -l" %}
{%- set random_password_generator='echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(100)))" | /usr/bin/python3' -%}

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

{%- if salt['cmd.shell'](check_mongo_auth_enabled) == 0 %}
/etc/mongod.conf:
  file.managed:
    - context:
      auth_enabled: false
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
(Assuming your user has access to view the combined cert/key file via group membership)

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
    - name: service mongod restart

# ALEX
# TODO: Purge invalid mongod users (not in pillar)
