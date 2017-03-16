{% set www_path='/srv/www' %}

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

/var/run/uwsgi.pid:
  file.managed:
    - group: {{ pillar['frontend-user'] }}
    - mode: 0644
    - replace: False
    - user: {{ pillar['frontend-user'] }}

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

{{ www_path }}:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ www_path }}/django:
  file.recurse:
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://service/django
    - user: root

{{ www_path }}/django/interface/media:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ www_path }}/django/interface/media-admin:
    file.directory:
    - group: {{ pillar['frontend-user'] }}
    - makedirs: False
    - mode: 0755
    - user: {{ pillar['frontend-user'] }}

{{ www_path }}/django/interface/static:
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
    - name: /usr/bin/python3 {{ www_path }}/django/manage.py makemigrations

django-migrate:
  cmd.run:
    - name: /usr/bin/python3 {{ www_path }}/django/manage.py migrate

{{ www_path }}/django/interface/sass/plugins:
    file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

{{ www_path }}/django/interface/sass/public/css:
    file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root

{{ www_path }}/django/interface/sass/public/font:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ www_path }}/django/interface/sass/public/js:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

{{ www_path }}/django/interface/static/sass:
  file.symlink:
    - target: {{ www_path}}/django/interface/sass/public

unzip-bootstrap:
  cmd:
    - run
    - name: 'unzip {{ www_path }}/django/sass/src/v4.0.0-alpha.6.zip -d {{ www_path }}/django/interface/sass/plugins'
    - unless: '[ -d {{ www_path }}/django/interface/sass/plugins/bootstrap-4.0.0-alpha.6 ]'

{{ www_path }}/django/interface/static/sass/plugins/bootstrap:
  file.symlink:
    - target: {{ www_path}}/django/interface/sass/plugins/bootstrap-4.0.0-alpha.6

unzip-fontawesome:
  cmd:
    - run
    - name: 'unzip {{ www_path }}/django/sass/src/font-awesome-4.7.0.zip -d {{ www_path }}/django/interface/sass/plugins'
    - unless: '[ -d {{ www_path }}/django/interface/sass/plugins/font-awesome-4.7.0 ]'

{{ www_path }}/django/interface/static/sass/plugins/font-awesome:
  file.symlink:
    - target: {{ www_path}}/django/interface/sass/plugins/font-awesome-4.7.0

#lessc %{buildroot}/usr/local/share/django/control/less/styles.less -x > %{buildroot}/usr/local/share/django/control/less/public/css/styles.min.css
#%{__cp} %{buildroot}/usr/local/share/django/control/less/public/css/styles.min.css %{buildroot}/usr/local/share/django/control/less/public/css/styles.min.css.RELEASE
#%{__cp} %{buildroot}/usr/local/share/django/control/less/bootstrap/dist/fonts/* %{buildroot}/usr/local/share/django/control/less/public/font
#%{__cp} %{buildroot}/usr/local/share/django/control/less/bootstrap/dist/js/bootstrap.min.js %{buildroot}/usr/local/share/django/control/less/public/js
#%{__cp} %{buildroot}/usr/local/share/django/control/less/font-awesome/fonts/* %{buildroot}/usr/local/share/django/control/less/public/font

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
      - file: {{ www_path }}/django
      - file: /etc/init.d/uwsgi
      - file: /etc/nginx/conf.d/*
      - file: /etc/uwsgi/vassals/django.ini
    - require:
      - sls: services/web
