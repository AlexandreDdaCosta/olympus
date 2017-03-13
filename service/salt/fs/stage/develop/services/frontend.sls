include:
  - base: services/frontend

/usr/local/bin/startserver.py:
  file.managed:
    - group: root
    - mode: 0755
    - source: salt://stage/develop/services/frontend/files/startserver.py
    - user: root
    - require:
      - sls: services/frontend

devserver-stop:
  cmd.run:
    - name: /usr/local/bin/killserver.sh

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
    - name: /usr/local/bin/startserver.py

nginx-develop:
  service.running:
    - enable: True
    - name: nginx
    - watch:
      - file: /etc/nginx/conf.d/django.conf
