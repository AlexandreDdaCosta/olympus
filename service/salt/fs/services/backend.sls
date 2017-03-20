{% set api_path=pillar.www_path+'/node' %}

include:
  - base: package
  - base: services/web

{% for packagename, package in pillar.get('backend-packages', {}).items() %}
{{ packagename }}-nodejs-web:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or package != None and 'version' not in package %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if package != None and 'version' in package %}
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

{% for packagename, package in pillar.get('backend-npm-packages', {}).items() %}
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
{{ packagename }}:
    npm.installed:
      - force_reinstall: True
{% elif package != None and 'version' in package %}
{{ packagename }}@{{ package['version'] }}:
    npm.installed:
{% else %}
{{ packagename }}:
    npm.installed:
{% endif %}
      - require:
        - sls: package
{% endfor %}

/etc/postgresql/9.6/main/pg_hba.conf:
  file.managed:
    - group: postgres
    - mode: 0640
    - source: salt://services/backend/files/pg_hba.conf
    - user: postgres

/usr/lib/tmpfiles.d/postgresql.conf:
  file.managed:
    - group: postgres
    - mode: 0600
    - source: salt://services/backend/files/postgresql.conf
    - user: postgres

postgresql:
  service.running:
    - enable: True
    - watch:
      - file: /etc/postgresql/9.6/main/pg_hba.conf
      - file: /usr/lib/tmpfiles.d/postgresql.conf
      - pkg: pgadmin3
      - pkg: postgresql-9.6
    - require:
      - sls: services/web
