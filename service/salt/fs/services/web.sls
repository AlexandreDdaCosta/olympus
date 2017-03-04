include:
  - base: package
  - base: security

{% for packagename, package in pillar.get('web-packages', {}).items() %}
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
      - sls: package
{% endfor %}

web_certs:
  cmd:
    - run
    - name: 'openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -out /etc/ssl/localcerts/server.crt -keyout /etc/ssl/localcerts/server.key -subj "/C=US/ST=Lake Worth/L=Lake Worth/O=FeralCanids/OU=Olympus web services/CN=feralcanids.com"'
{% if pillar.refresh_security is not defined or not pillar.refresh_security %}
    - unless: 'test -f /etc/ssl/localcerts/server.crt && openssl verify /etc/ssl/localcerts/server.crt'
{% endif %}

nginx:
  service.running:
    - watch:
      - file: /etc/nginx/conf.d/default.conf
  file.managed:
    - name: /etc/nginx/conf.d/default.conf
    - source: salt://services/web/files/default.conf
