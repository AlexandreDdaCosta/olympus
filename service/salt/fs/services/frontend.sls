{% set project_path=pillar.www_path+'/django/interface' %}
{% set sass_path=project_path+'/sass' %}

include:
  - base: package
  - base: services/web

{% for packagename, package in pillar.get('frontend-packages', {}).items() %}
{{ packagename }}-frontend:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or package != None and 'version' not in package or package == None %}
  pkg.latest:
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
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
    - name: {{ packagename }} {{ package['version'] }}
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
    - version: {{ package['version'] }}
{% endif %}
    - require:
      - sls: package
{% endfor %}

frontend-group:
  group.present:
    - name: {{ pillar['frontend-user'] }}
    - system: True

frontend-user:
  user.present:
    - createhome: True
    - fullname: {{ pillar['frontend-user'] }}
    - name: {{ pillar['frontend-user'] }}
    - shell: /bin/false
    - home: /home/{{ pillar['frontend-user'] }}
    - groups:
      - {{ pillar['frontend-user'] }}

/etc/uwsgi/vassals:
    file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

/etc/uwsgi.ini:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/frontend/files/uwsgi.ini
    - user: root

/etc/rc0.d/K01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc1.d/K01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc2.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc3.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc4.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc5.d/S01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/rc6.d/K01uwsgi:
  file.symlink:
    - target: /etc/init.d/uwsgi

/etc/init.d/uwsgi:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/frontend/files/init.uwsgi
    - user: root

/etc/logrotate.d/uwsgi:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://services/frontend/files/logrotate.uwsgi
    - user: root

/var/log/uwsgi.log:
  file.managed:
    - group: {{ pillar['frontend-user'] }}
    - mode: 0644
    - replace: False
    - user: {{ pillar['frontend-user'] }}

/etc/nginx/conf.d/django.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/frontend/files/django.conf
    - user: root

/etc/uwsgi/vassals/django.ini:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://services/frontend/files/django.ini
    - user: root

{{ pillar.www_path }}/django:
  file.recurse:
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://service/django
    - user: root

{{ project_path }}/media:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ project_path }}/media/blog:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ project_path }}/media-admin:
    file.directory:
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['frontend-user'] }}

{{ project_path }}/static:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ project_path }}/static/js:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

/usr/local/bin/killserver.sh:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://services/frontend/files/killserver.sh
    - user: root

frontend-devserver-stop:
  cmd.run:
    - name: /usr/local/bin/killserver.sh

django-makemigrations:
  cmd.run:
    - name: yes | /usr/bin/python3 {{ pillar.www_path }}/django/manage.py makemigrations

django-migrate:
  cmd.run:
    - name: yes | /usr/bin/python3 {{ pillar.www_path }}/django/manage.py migrate

{{ sass_path }}/public/css:
    file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

{{ sass_path }}/public/font:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ sass_path }}/public/js:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ sass_path }}/src:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ project_path }}/static/sass:
  file.symlink:
    - target: {{ sass_path}}/public

tether-get:
  cmd:
    - run
    - name: 'wget http://github.com/HubSpot/tether/archive/v1.3.3.zip -O {{ sass_path }}/src/v1.3.3.zip'
    - unless: '[ -f {{ sass_path }}/src/v1.3.3.zip ]'

tether:
  cmd:
    - run
    - name: 'unzip {{ sass_path }}/src/v1.3.3.zip -d {{ sass_path }}'
    - unless: '[ -d {{ sass_path }}/tether-1.3.3 ]'

{{ sass_path }}/tether:
  file.symlink:
    - target: {{ sass_path}}/tether-1.3.3

{{ sass_path}}/public/js/tether.min.js:
  file.managed:
    - source: {{ sass_path }}/tether/dist/js/tether.min.js

bootstrap-get:
  cmd:
    - run
    - name: 'wget https://github.com/twbs/bootstrap/archive/v4.0.0-alpha.6.zip -O {{ sass_path }}/src/v4.0.0-alpha.6.zip'
    - unless: '[ -f {{ sass_path }}/src/v4.0.0-alpha.6.zip ]'

bootstrap:
  cmd:
    - run
    - name: 'unzip {{ sass_path }}/src/v4.0.0-alpha.6.zip -d {{ sass_path }}'
    - unless: '[ -d {{ sass_path }}/bootstrap-4.0.0-alpha.6 ]'

{{ sass_path }}/bootstrap:
  file.symlink:
    - target: {{ sass_path}}/bootstrap-4.0.0-alpha.6

{{ sass_path}}/public/js/bootstrap.min.js:
  file.managed:
    - source: {{ sass_path }}/bootstrap/dist/js/bootstrap.min.js

fontawesome-get:
  cmd:
    - run
    - name: 'wget http://fontawesome.io/assets/font-awesome-4.7.0.zip -O {{ sass_path }}/src/font-awesome-4.7.0.zip'
    - unless: '[ -f {{ sass_path }}/src/font-awesome-4.7.0.zip ]'

fontawesome:
  cmd:
    - run
    - name: 'unzip {{ sass_path }}/src/font-awesome-4.7.0.zip -d {{ pillar.www_path }}/django/interface/sass'
    - unless: '[ -d {{ sass_path }}/font-awesome-4.7.0 ]'

{{ sass_path }}/font-awesome:
  file.symlink:
    - target: {{ sass_path }}/font-awesome-4.7.0

font-awesome-fonts:
  cmd:
    - run
    - name: 'cp -p {{ sass_path }}/font-awesome/fonts/* {{ sass_path }}/public/font'

sass-css:
  cmd:
    - run
    - name: 'sass --style compressed {{ sass_path }}/styles.scss > {{ sass_path}}/public/css/styles.min.css'

sass-css-full:
  cmd:
    - run
    - name: 'sass {{ sass_path }}/styles.scss > {{ sass_path}}/public/css/styles.css'

{{ sass_path}}/public/css/styles.min.css.RELEASE:
  file.managed:
    - source: {{ sass_path }}/public/css/styles.min.css

jquery:
  cmd:
    - run
    - name: 'curl https://code.jquery.com/jquery-3.2.0.min.js > {{ project_path }}/static/js/jquery-3.2.0.min.js'
    - unless: '[ -f {{ project_path }}/static/js/jquery-3.2.0.min.js ]'

{{ project_path }}/static/js/jquery.min.js:
  file.symlink:
    - target: {{ project_path }}/static/js/jquery-3.2.0.min.js

{% for username, user in pillar.get('users', {}).items() %}
{% if user['is_staff'] %}
{{ username }}-django_admin:
{% if 'email_address' in user %}
{% set django_admin_email=user['email_address'] %}
{% else %}
{% set django_admin_email=pillar.core_email %}
{% endif %}
  cmd.run:
    - name: sudo /usr/bin/python3 {{ pillar.www_path }}/django/manage.py verifyuser --username {{ username }} --email {{ django_admin_email }} --password {{ salt['cmd.shell'](random_string_generator) }} --admin --superuser
{% endif %}
{% endfor %}

nginx-frontend:
  service.running:
    - name: nginx
    - watch:
      - file: /etc/nginx/conf.d/django.conf

frontend-uwsgi:
  service.running:
    - enable: True
    - name: uwsgi
    - watch:
      - file: {{ pillar.www_path }}/django
      - file: /etc/init.d/uwsgi
      - file: /etc/nginx/conf.d/django.conf
      - file: /etc/uwsgi/vassals/django.ini
    - require:
      - sls: services/web
