{% set frontend_path=pillar.www_path+'/django/interface' %}
{% set frontend_sass_path=frontend_path+'/sass' %}
{%- set random_password_generator='echo "import random; import string; print(\'\'.join(random.choice(string.ascii_letters + string.digits) for x in range(100)))" | /usr/bin/python3' -%}

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

/var/log/django:
  file.directory:
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['frontend-user'] }}

/var/log/django/django.log:
  file.managed:
    - group: {{ pillar['frontend-user'] }}
    - mode: 0644
    - replace: False
    - user: {{ pillar['frontend-user'] }}

/etc/nginx/conf.d/interface.conf:
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
/etc/uwsgi/vassals/django.ini:
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

{{ frontend_path }}/media:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ frontend_path }}/media/blog:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ frontend_path }}/media-admin:
  file.directory:
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['frontend-user'] }}

{{ frontend_path }}/static:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ frontend_path }}/static/js:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

frontend_conf_file:
  file.managed:
    - dir_mode: 0755
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0640
    - name: {{ frontend_path }}/settings_local.py
    - source: salt://services/frontend/settings_local.jinja
    - template: jinja
    - user: {{ pillar['frontend-user'] }}

frontend_wsgi_app_file:
  file.managed:
    - dir_mode: 0755
    - group: root
    - makedirs: False
    - mode: 0644
    - name: {{ frontend_path }}/wsgi.py
    - source: salt://services/frontend/wsgi.py.jinja
    - template: jinja
    - user: root

django-makemigrations:
  cmd.run:
    - name: yes | /usr/bin/python3 {{ pillar.www_path }}/django/manage.py makemigrations

django-migrate:
  cmd.run:
    - name: yes | /usr/bin/python3 {{ pillar.www_path }}/django/manage.py migrate

{{ frontend_sass_path }}/public/css:
    file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

{{ frontend_sass_path }}/public/font:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ frontend_sass_path }}/public/js:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ frontend_sass_path }}/src:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ frontend_path }}/static/sass:
  file.symlink:
    - target: {{ frontend_sass_path }}/public

tether-get:
  cmd:
    - run
    - name: 'wget http://github.com/HubSpot/tether/archive/v1.4.3.zip -O {{ frontend_sass_path }}/src/v1.4.3.zip'
    - unless: '[ -f {{ frontend_sass_path }}/src/v1.4.3.zip ]'

tether:
  cmd:
    - run
    - name: 'unzip {{ frontend_sass_path }}/src/v1.4.3.zip -d {{ frontend_sass_path }}'
    - unless: '[ -d {{ frontend_sass_path }}/tether-1.4.3 ]'

{{ frontend_sass_path }}/tether:
  file.symlink:
    - target: {{ frontend_sass_path}}/tether-1.4.3

{{ frontend_sass_path}}/public/js/tether.min.js:
  file.managed:
    - source: {{ frontend_sass_path }}/tether/dist/js/tether.min.js

bootstrap-get:
  cmd:
    - run
    - name: 'wget https://github.com/twbs/bootstrap/archive/v4.5.0.zip -O {{ frontend_sass_path }}/src/v4.5.0.zip'
    - unless: '[ -f {{ frontend_sass_path }}/src/v4.5.0.zip ]'

bootstrap:
  cmd:
    - run
    - name: 'unzip {{ frontend_sass_path }}/src/v4.5.0.zip -d {{ frontend_sass_path }}'
    - unless: '[ -d {{ frontend_sass_path }}/bootstrap-4.5.0 ]'

{{ frontend_sass_path }}/bootstrap:
  file.symlink:
    - target: {{ frontend_sass_path}}/bootstrap-4.5.0

{{ frontend_sass_path}}/public/js/bootstrap.min.js:
  file.managed:
    - source: {{ frontend_sass_path }}/bootstrap/dist/js/bootstrap.min.js

fontawesome-get:
  cmd:
    - run
    - name: 'wget https://use.fontawesome.com/releases/v5.13.0/fontawesome-free-5.13.0-web.zip -O {{ frontend_sass_path }}/src/fontawesome-free-5.13.0-web.zip'
    - unless: '[ -f {{ frontend_sass_path }}/src/fontawesome-free-5.13.0-web.zip ]'

fontawesome:
  cmd:
    - run
    - name: 'unzip {{ frontend_sass_path }}/src/fontawesome-free-5.13.0-web.zip -d {{ pillar.www_path }}/django/interface/sass'
    - unless: '[ -d {{ frontend_sass_path }}/fontawesome-free-5.13.0-web ]'

{{ frontend_sass_path }}/font-awesome:
  file.symlink:
    - target: {{ frontend_sass_path }}/fontawesome-free-5.13.0-web

font-awesome-fonts:
  cmd:
    - run
    - name: 'cp -p {{ frontend_sass_path }}/font-awesome/webfonts/* {{ frontend_sass_path }}/public/font'

sass-css:
  cmd:
    - run
    - name: 'sass --style compressed {{ frontend_sass_path }}/styles.scss > {{ frontend_sass_path }}/public/css/styles.min.css'

sass-css-full:
  cmd:
    - run
    - name: 'sass {{ frontend_sass_path }}/styles.scss > {{ frontend_sass_path }}/public/css/styles.css'

{{ frontend_sass_path }}/public/css/styles.min.css.RELEASE:
  file.managed:
    - source: {{ frontend_sass_path }}/public/css/styles.min.css

jquery:
  cmd:
    - run
    - name: 'curl https://code.jquery.com/jquery-3.5.1.min.js > {{ frontend_path }}/static/js/jquery-3.5.1.min.js'
    - unless: '[[ -f {{ frontend_path }}/static/js/jquery-3.2.0.min.js && ! -s {{ frontend_path }}/static/js/jquery-3.2.0.min.js ]]'

{{ frontend_path }}/static/js/jquery.min.js:
  file.symlink:
    - target: {{ frontend_path }}/static/js/jquery-3.5.1.min.js

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
    - name: sudo /usr/bin/python3 {{ pillar.www_path }}/django/manage.py verifyuser --username {{ username }} --email {{ django_admin_email }} --password {{ django_password }} --admin --superuser --resave
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
      - file: /etc/nginx/conf.d/interface.conf

frontend-uwsgi:
  service.running:
    - name: uwsgi
    - watch:
      - file: {{ pillar.www_path }}/django
      - file: /etc/nginx/conf.d/interface.conf
{%- if grains.get('stage') and grains.get('stage') != 'develop' %}
      - file: /etc/uwsgi/vassals/django.ini
{%- endif %}
      - file: {{ frontend_path }}/settings_local.py
    - require:
      - sls: web

{% endif %}
