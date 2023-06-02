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
    - group: root
    - mode: 0755
    - user: root

/usr/local/bin/olympus/startserver.py:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/startserver.py
    - user: root
    - require:
      - sls: services/frontend

/usr/local/bin/olympus/killserver.sh:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://services/frontend/files/killserver.sh
    - user: root

devserver-stop:
  cmd.run:
    - name: /usr/local/bin/olympus/killserver.sh

{# Placed here 
frontend-uwsgi-stop:
  service.dead:
    - name: uwsgi

develop-django.conf:
  file.managed:
    - group: root
    - name: /etc/nginx/conf.d/django.conf
    - makedirs: False
    - mode: 0644
    - source: salt://stage/develop/services/frontend/files/django.conf
    - user: root

devserver-start:
  cmd.run:
    - name: /usr/local/bin/olympus/startserver.py

nginx-develop:
  service.running:
    - enable: True
    - name: nginx
    - watch:
      - file: /etc/nginx/conf.d/django.conf

{% endif %}
{% endif %}
