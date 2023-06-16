{% set pgadmin_path=pillar.docker_services_path+'/pgadmin' %}
{% set pgadmin_admin_password_file_name='pgadmin_admin_password' %}
{% set random_pgadmin_password='echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(50)))" | /usr/bin/python3' %}

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

olympus.db:
  postgres_database.present:
    - name: olympus

frontend_app_data.db:
  postgres_database.present:
    - name: app_data

frontend-user_data.db:
  postgres_database.present:
    - name: user_data

frontend_db_user:
  postgres_user.present:
    - default_password: 'md5{MD5OF({{ pillar['random_key']['frontend_db_key'] }})}'
    - encrypted: True
    - name: {{ pillar['frontend-user'] }}

frontend_db_user_pwd_reset:
  cmd.run:
    - name: salt '{{ grains.get('localhost') }}' credentials.interface_backend
    - require: 
      - frontend_db_user

frontend_app_data_privs:
  postgres_privileges.present:
    - name: {{ pillar['frontend-user'] }}
    - object_name: app_data
    - object_type: database
    - privileges:
      - ALL

frontend-user_data_privs:
  postgres_privileges.present:
    - name: {{ pillar['frontend-user'] }}
    - object_name: user_data
    - object_type: database
    - privileges:
      - ALL

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

pgadmin_docker_compose_file:
  file.managed:
    - context:
      pgadmin_default_password_file: {{ pgadmin_admin_password_file_name }}
    - group: root
    - makedirs: False
    - mode: 0644
    - name: {{ pgadmin_path }}/docker-compose.yml
    - source: salt://services/database/pgadmin.docker-compose.yml.jinja
    - template: jinja
    - user: root

{% set default_admin_password_file_name = pgadmin_path ~ "/" ~ pgadmin_admin_password_file_name %}
{% if not salt['file.file_exists' ](default_admin_password_file_name) %}
{{ default_admin_password_file_name }}:
  file.managed:
    - context:
      default_pgadmin_password: {{ salt['cmd.shell'](random_pgadmin_password) }}
    - group: pgadmin
    - makedirs: False
    - mode: 0600
    - source: salt://services/database/pgadmin_default_admin_password.jinja
    - template: jinja
    - user: pgadmin
{% endif %}

{% endif %}
