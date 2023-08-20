{% set pgadmin_path=pillar.docker_services_path+'/pgadmin' %}
{% set random_pgadmin_password='echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(50)))" | /usr/bin/python3' %}
{% set pgadmin_default_password=salt['cmd.shell'](random_pgadmin_password) %}

include:
  - base: package
  - base: services
  - base: web

{# Sanity check for inattentive administrators #}
{%- if grains.get('server') == 'database' or grains.get('server') == 'unified' %}

{% for packagename, package in pillar.get('database-packages', {}).items() %}
{{ packagename }}-database-pkgs:
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
{% endfor %}

{% for application, image in pillar.get('database-docker-images', {}).items() %}
{{ image['image'] }}:
  docker_image.present:
    - client_timeout: 60
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - tag: latest
    - force: True
{% elif 'tag' in image %}
    - tag: {{ image['tag'] }}
{% else %}
    - tag: latest
{% endif %}
{% endfor %}

systmctl_disable_apache2:
  cmd.run:
    - name: service apache2 stop; systemctl disable apache2

/etc/postgresql/14/main/pg_hba.conf:
  file.managed:
    - group: postgres
    - mode: 0640
    - source: salt://services/database/pg_hba.conf.jinja
    - template: jinja
    - user: postgres

/etc/postgresql/14/main/postgresql.conf:
  file.managed:
    - group: postgres
    - mode: 0600
    - source: salt://services/database/postgresql.conf.jinja
    - template: jinja
    - user: postgres

postgresql:
  service.running:
    - enable: True
    - watch:
      - file: /etc/postgresql/14/main/pg_hba.conf
      - file: /etc/postgresql/14/main/postgresql.conf
      - pkg: postgresql-14

frontend_db_user:
  postgres_user.present:
    - default_password: 'md5{MD5OF({{ pillar['random_key']['frontend_db_key'] }})}'
    - encrypted: True
    - name: {{ pillar['frontend_user'] }}

{% for dbid, database in pillar.get('frontend_databases', {}).items() %}
frontend_{{ dbid }}_database:
  postgres_database.present:
    - name: {{ database['name'] }}

frontend_{{ dbid }}_database_privileges:
  postgres_privileges.present:
    - name: {{ database['user'] }}
    - object_name: {{ database['name'] }}
    - object_type: database
    - privileges:
      - ALL
{% endfor %}

frontend_db_user_pwd_reset:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' credentials.interface_backend
    - require: 
      - frontend_db_user

/var/log/pgadmin:
  file.directory:
    - group: pgadmin
    - mode: 0700
    - user: pgadmin

{{ pgadmin_path }}:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ pillar['pgadmin_lib_path'] }}:
  file.directory:
    - group: pgadmin
    - makedirs: False
    - mode: 0755
    - user: pgadmin

{{ pillar['pgadmin_storage_path'] }}:
  file.directory:
    - group: pgadmin
    - makedirs: False
    - mode: 0755
    - user: pgadmin

pgadmin_docker_compose_file:
  file.managed:
    - context:
      pgadmin_default_password: {{ pgadmin_default_password }}
      pgadmin_path: {{ pgadmin_path }}
    - group: root
    - makedirs: False
    - mode: 0644
    - name: {{ pgadmin_path }}/docker-compose.yml
    - source: salt://services/database/pgadmin.docker-compose.yml.jinja
    - template: jinja
    - user: root

{{ pgadmin_path }}/servers.json:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/database/servers.json.jinja
    - template: jinja
    - user: root

/lib/systemd/system/pgadmin.service:
  file.managed:
    - context:
      docker_compose_file: {{ pgadmin_path }}/docker-compose.yml
    - group: root
    - makedirs: False
    - mode: 0644
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/database/pgadmin.service.jinja
    - template: jinja
    - user: root

pgadmin-service:
  service.running:
    - enable: True
    - name: pgadmin
    - watch:
      - file: /lib/systemd/system/pgadmin.service
      - file: {{ pgadmin_path }}/docker-compose.yml
      - file: {{ pgadmin_path }}/servers.json

{# pgadmin user management section #}

{% for user, userdata in pillar.get('users', {}).items() %}
{% if ( (user == 'pgadmin') or
        ('is_staff' in userdata and userdata['is_staff']) ) %}
{% if 'email_address' in userdata %}

{# User /pgpass files #}

{{ user }}_pgpass_file:
  file.managed:
    - group: pgadmin
    - mode: 0600
    - name: {{ pillar['pgadmin_lib_path'] }}/storage/{{ pillar['users'][user]['email_address'] | regex_replace('@', '_') }}/pgpass
    - source: salt://services/database/pgpass.jinja
    - template: jinja
    - user: pgadmin

{{ user }}_pgpass_password:
  module.run:
    - pgadmin.pgpass_frontend_password:
      - file_name: {{ pillar['pgadmin_lib_path'] }}/storage/{{ pillar['users'][user]['email_address'] | regex_replace('@', '_') }}/pgpass

{% endif %}
{% endif %}
{% endfor %}

{# User SQLite database entries #}

pgadmin.pgadmin_db_user:
  module.run

{% endif %}

{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
pgadmin.upgrade:
  module.run
{% endif %}

