{% set frontend_conf_file_name = pillar['frontend_conf_file_name'] -%}
{% set frontend_password_file_name = pillar['frontend_password_file_name'] -%}
{% set get_frontend_passwd = 'unset password; if [ -f ' + pillar['frontend_password_file_name'] + ' ]; then password=`cat' + pillar['frontend_password_file_name'] + '`; echo $password; fi;' -%}
{% set current_frontend_password = salt['cmd.shell'](get_frontend_passwd) -%}
{% set django_vassal_file = pillar['nginx_vassals_directory'] + '/django.ini' -%}
{% set random_password_generator = 'echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(100)))" | /usr/bin/python3' -%}

include:
  - base: package
  - base: web

{# Sanity check for inattentive administrators #}
{%- if grains.get('server') == 'interface' or grains.get('server') == 'unified' %}

{% for packagename, package in pillar.get('frontend-packages', {}).items() %}
{{ packagename }}-frontend:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or package != None and 'version' not in package or package == None %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
    - name: {{ packagename }}
{% if package != None and 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('frontend-pip3-packages', {}).items() %}
{{ packagename }}:
  pip.installed:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - name: {{ packagename }}
    - upgrade: True
{% elif package != None and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - name: {{ packagename }} {{ package['version'] }}
    {% else %}
    - name: {{ packagename }}
    {% endif %}
{% else %}
    - name: {{ packagename }}
{% endif %}
    - bin_env: '/usr/bin/pip3'
    - require:
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('frontend-gems', {}).items() %}
{{ packagename }}:
  gem.installed:
{% if package != None and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
    - require:
      - sls: package
{% endfor %}

{{ pillar['system_log_directory'] }}/django:
  file.directory:
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['frontend-user'] }}

{{ pillar['system_log_directory'] }}/django/django.log:
  file.managed:
    - group: {{ pillar['frontend-user'] }}
    - mode: 0644
    - replace: False
    - user: {{ pillar['frontend-user'] }}

{{ pillar['frontend_nginx_conf_file_name'] }}:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/frontend/interface.conf.jinja
    - template: jinja
    - user: root

{# 
   Added stage check here to avoid conflicts in development stage.
   uWSGI runs everywhere.
#}
{% if grains.get('stage') and grains.get('stage') != 'develop' %}
{{ django_vassal_file }}:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/frontend/files/django.ini
    - user: root
{% endif %}

{{ pillar.www_path }}/django:
  file.recurse:
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://service/django
    - user: root

{{ pillar['olympus-app-package-path'] }}/django_blog_olympus:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://blog
    - user: root

{{ pillar['olympus-app-package-path'] }}/django_album_olympus:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://album
    - user: root

{{ pillar['frontend_path'] }}/media:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ pillar['frontend_path'] }}/media/blog:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ pillar['frontend_path'] }}/media-admin:
  file.directory:
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['frontend-user'] }}

{{ pillar['frontend_path'] }}/static:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ pillar['frontend_path'] }}/static/js:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{% if salt['file.file_exists' ](frontend_password_file_name) %}
    {% set frontend_password = current_frontend_password %}
{% else %}
    {% set frontend_password = pillar['random_key']['frontend_db_key'] %}
{% endif %}
{{ frontend_conf_file_name }}:
  file.managed:
    - context:
      frontend_db_key: {{ frontend_password }}
    - dir_mode: 0755
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0640
    - source: salt://services/frontend/settings_local.jinja
    - template: jinja
    - user: {{ pillar['frontend-user'] }}

frontend_wsgi_app_file:
  file.managed:
    - dir_mode: 0755
    - group: root
    - makedirs: False
    - mode: 0644
    - name: {{ pillar['frontend_path'] }}/wsgi.py
    - source: salt://services/frontend/wsgi.py.jinja
    - template: jinja
    - user: root

django-makemigrations:
  cmd.run:
    - name: yes | /usr/bin/python3 {{ pillar['frontend_path_root'] }}/manage.py makemigrations

django-migrate:
  cmd.run:
    - name: yes | /usr/bin/python3 {{ pillar['frontend_path_root'] }}/manage.py migrate

{{ pillar['frontend_sass_path'] }}/public/css:
  file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

{{ pillar['frontend_sass_path'] }}/public/font:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ pillar['frontend_sass_path'] }}/public/js:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ pillar['frontend_sass_path'] }}/src:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ pillar['frontend_path'] }}/static/sass:
  file.symlink:
    - target: {{ pillar['frontend_sass_path'] }}/public

tether-get:
  cmd:
    - run
    - name: 'wget http://github.com/HubSpot/tether/archive/v1.4.3.zip -O {{ pillar['frontend_sass_path'] }}/src/v1.4.3.zip'
    - unless: '[ -f {{ pillar['frontend_sass_path'] }}/src/v1.4.3.zip ]'

tether:
  cmd:
    - run
    - name: 'unzip {{ pillar['frontend_sass_path'] }}/src/v1.4.3.zip -d {{ pillar['frontend_sass_path'] }}'
    - unless: '[ -d {{ pillar['frontend_sass_path'] }}/tether-1.4.3 ]'

{{ pillar['frontend_sass_path'] }}/tether:
  file.symlink:
    - target: {{ pillar['frontend_sass_path']}}/tether-1.4.3

{{ pillar['frontend_sass_path']}}/public/js/tether.min.js:
  file.managed:
    - source: {{ pillar['frontend_sass_path'] }}/tether/dist/js/tether.min.js

bootstrap-get:
  cmd:
    - run
    - name: 'wget https://github.com/twbs/bootstrap/archive/v4.5.0.zip -O {{ pillar['frontend_sass_path'] }}/src/v4.5.0.zip'
    - unless: '[ -f {{ pillar['frontend_sass_path'] }}/src/v4.5.0.zip ]'

bootstrap:
  cmd:
    - run
    - name: 'unzip {{ pillar['frontend_sass_path'] }}/src/v4.5.0.zip -d {{ pillar['frontend_sass_path'] }}'
    - unless: '[ -d {{ pillar['frontend_sass_path'] }}/bootstrap-4.5.0 ]'

{{ pillar['frontend_sass_path'] }}/bootstrap:
  file.symlink:
    - target: {{ pillar['frontend_sass_path']}}/bootstrap-4.5.0

{{ pillar['frontend_sass_path']}}/public/js/bootstrap.min.js:
  file.managed:
    - source: {{ pillar['frontend_sass_path'] }}/bootstrap/dist/js/bootstrap.min.js

fontawesome-get:
  cmd:
    - run
    - name: 'wget https://use.fontawesome.com/releases/v5.13.0/fontawesome-free-5.13.0-web.zip -O {{ pillar['frontend_sass_path'] }}/src/fontawesome-free-5.13.0-web.zip'
    - unless: '[ -f {{ pillar['frontend_sass_path'] }}/src/fontawesome-free-5.13.0-web.zip ]'

fontawesome:
  cmd:
    - run
    - name: 'unzip {{ pillar['frontend_sass_path'] }}/src/fontawesome-free-5.13.0-web.zip -d {{ pillar.www_path }}/django/interface/sass'
    - unless: '[ -d {{ pillar['frontend_sass_path'] }}/fontawesome-free-5.13.0-web ]'

{{ pillar['frontend_sass_path'] }}/font-awesome:
  file.symlink:
    - target: {{ pillar['frontend_sass_path'] }}/fontawesome-free-5.13.0-web

font-awesome-fonts:
  cmd:
    - run
    - name: 'cp -p {{ pillar['frontend_sass_path'] }}/font-awesome/webfonts/* {{ pillar['frontend_sass_path'] }}/public/font'

sass-css:
  cmd:
    - run
    - name: 'sass --style compressed {{ pillar['frontend_sass_path'] }}/styles.scss > {{ pillar['frontend_sass_path'] }}/public/css/styles.min.css'

sass-css-full:
  cmd:
    - run
    - name: 'sass {{ pillar['frontend_sass_path'] }}/styles.scss > {{ pillar['frontend_sass_path'] }}/public/css/styles.css'

{{ pillar['frontend_sass_path'] }}/public/css/styles.min.css.RELEASE:
  file.managed:
    - source: {{ pillar['frontend_sass_path'] }}/public/css/styles.min.css

jquery:
  cmd:
    - run
    - name: 'curl https://code.jquery.com/jquery-3.5.1.min.js > {{ pillar['frontend_path'] }}/static/js/jquery-3.5.1.min.js'
    - unless: '[[ -f {{ pillar['frontend_path'] }}/static/js/jquery-3.2.0.min.js && ! -s {{ pillar['frontend_path'] }}/static/js/jquery-3.2.0.min.js ]]'

{{ pillar['frontend_path'] }}/static/js/jquery.min.js:
  file.symlink:
    - target: {{ pillar['frontend_path'] }}/static/js/jquery-3.5.1.min.js

{% for username, user in pillar.get('users', {}).items() %}
{% if 'is_staff' in user and user['is_staff'] %}
{{ username }}-django_admin:
{% if 'email_address' in user %}
{% set django_admin_email=user['email_address'] %}
{% else %}
{% set django_admin_email=pillar.core_email %}
{% endif %}
{% if 'original_interface_password' in user %}
{% set django_password=user['original_interface_password'] %}
{% else %}
{% set django_password=salt['cmd.shell'](random_password_generator) %}
{% endif %}
  cmd.run:
    - name: sudo /usr/bin/python3 {{ pillar.frontend_path_root }}/manage.py verifyuser --username {{ username }} --email {{ django_admin_email }} --password {{ django_password }} --admin --superuser --resave
{% endif %}
{% endfor %}

frontend-cert:
  cmd:
    - run
    - name: sudo service nginx stop; sudo /usr/bin/certbot certonly --quiet --standalone -d {{ pillar['core-domain-CN'] }} -d www.{{ pillar['core-domain-CN'] }} --agree-tos -m {{ pillar['core-email'] }} 
    - unless: 'test -f /etc/letsencrypt/live/{{ pillar['core-domain-CN'] }}/fullchain.pem'

frontend_cert_renewal:
  cmd.run:
    - name: /usr/bin/certbot renew --post-hook "service nginx restart"
{# 
The old command was invariably giving this issue at renew time:

Domain: <core-domain-CN>
Type:   connection
Detail: 192.64.119.62: Fetching https://www.<core-domain-CN>:
Connection refused

NOTE that <core-domain-CN> is a placeholder; see actual value in pillar.

Best GUESS at culprit is the pre-hook command. I've that since renewal works correctly first time without.
Also removed the "--http-01-port" specification since it appears to serve no purpose; i.e., 80 is the default.

- name: /usr/bin/certbot renew --pre-hook "service nginx stop" --post-hook "service nginx start" --http-01-port 80
#}

nginx-frontend:
  service.running:
    - name: nginx
    - watch:
      - file: {{ pillar.frontend_nginx_conf_file_name }}

frontend-uwsgi:
  service.running:
    - name: uwsgi
    - watch:
      - file: {{ pillar.www_path }}/django
      - file: {{ pillar.frontend_nginx_conf_file_name }}
{%- if grains.get('stage') and grains.get('stage') != 'develop' %}
      - file: {{ django_vassal_file }}
{%- endif %}
      - file: {{ frontend_conf_file_name }}
    - require:
      - sls: web

{% endif %}
