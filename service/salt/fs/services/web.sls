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

ca.cnf:
  file.managed:
    - group: root
    - mode: 600
    - name: /etc/ssl/localcerts/ca.cnf
    - source: salt://web/ca.cnf.jinja
    - template: jinja
    - user: root
  cmd.run:
    - name: 'openssl req -new -x509 -days 9999 -config /etc/ssl/localcerts/ca.cnf -keyout /etc/ssl/localcerts/ca-key.pem -out /etc/ssl/localcerts/ca-crt.pem'

local_certs:
  cmd:
    - run
    - name: 'openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -out /etc/ssl/localcerts/server.crt -keyout /etc/ssl/localcerts/server.key -subj "/C={{ pillar['core-domain-C'] }}/ST={{ pillar['core-domain-ST'] }}/L={{ pillar['core-domain-L'] }}/O={{ pillar['core-domain-O'] }}/OU={{ pillar['core-domain-OU'] }}/CN={{ pillar['core-domain-CN'] }}"'
{% if pillar.refresh_security is not defined or not pillar.refresh_security %}
    - unless: 'test -f /etc/ssl/localcerts/server.crt && openssl verify /etc/ssl/localcerts/server.crt'
{% endif %}

{{ pillar.www_path }}:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

nginx:
  service.running:
    - watch:
      - file: /etc/nginx/conf.d/default.conf
  file.managed:
    - name: /etc/nginx/conf.d/default.conf
    - source: salt://services/web/files/default.conf
