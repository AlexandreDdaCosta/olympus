include:
  - base: services/frontend

{# Sanity checks for inattentive administrators #}
{% if grains.get('stage') and grains.get('stage') == 'develop' %}
{% if grains.get('server') == 'interface' or grains.get('server') == 'unified' %}

{# Enable permanent dev server on highstate run by setting "stage" grain. Useful commands:

sudo -i salt '*' grains.setval stage develop
sudo -i salt '*' grains.delval stage

Currently the dev server does not restart automatically on server shutdown, unlike the
full uWSGI server.
#}

/etc/logrotate.d/devserver:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://stage/develop/services/frontend/files/logrotate.devserver
    - user: root

/var/log/devserver:
  file.directory:
    - group: uwsgi
    - mode: 0755
    - user: uwsgi

/usr/local/bin/olympus/startserver.py:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/startserver.py
    - user: root

/usr/local/bin/olympus/killserver.sh:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/killserver.sh
    - user: root

/etc/init.d/django-devserver:
    file.managed:
    - group: root
    - makedirs: False
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/init.django-devserver
    - user: root

develop-django.conf:
  file.managed:
    - group: root
    - name: /etc/nginx/conf.d/django.conf
    - makedirs: False
    - mode: 0644
    - source: salt://stage/develop/services/frontend/files/django.conf
    - user: root

web-django-devserver:
  service.running:
    - enable: True
    - name: django-devserver
    - watch:
      - file: /etc/init.d/django-devserver

{% endif %}
{% endif %}
