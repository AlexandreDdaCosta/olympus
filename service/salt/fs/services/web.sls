include:
  - base: repository
  - base: package
  - base: security

{% for packagename, package in pillar.get('web-service-packages', {}).items() %}
{{ packagename }}-web:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or 'version' not in package %}
  pkg.latest:
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
    - name: {{ packagename }}
{% if 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: repository
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('web-service-pip-packages', {}).items() %}
{{ packagename }}:
  pip.installed:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - name: {{ packagename }}
    - upgrade: True
{% elif 'version' in package %}
    - name: {{ packagename }} {{ package['version'] }}
{% else %}
    - name: {{ packagename }}
{% endif %}
    - require:
      - sls: repository
      - sls: package
{% endfor %}

web_certs:
  cmd:
    - run
    - name: 'openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -out /etc/ssl/localcerts/server.crt -keyout /etc/ssl/localcerts/server.key'
    - unless: 'test -e /etc/ssl/localcerts/server.crt && test -e /etc/ssl/localcerts/server.key'

nginx:
  service.running:
    - watch:
      - file: /etc/nginx/conf.d/default.conf
  file.managed:
    - name: /etc/nginx/conf.d/default.conf
    - source: salt://services/web/files/default.conf
