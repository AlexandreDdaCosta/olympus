include:
  - base: package
  - base: services/web

{% for packagename, package in pillar.get('nodejs-web-service-packages', {}).items() %}
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

{% for packagename, package in pillar.get('nodejs-web-service-npm-packages', {}).items() %}
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
{{ packagename }}:
    npm.installed:
      - force_reinstall: True
{% elif package != None and 'version' in package %}
{{ packagename }}@{{ package['version'] }}:
    npm.installed
{% else %}
{{ packagename }}:
    npm.installed
{% endif %}
{% endfor %}
      - require:
        - sls: package
