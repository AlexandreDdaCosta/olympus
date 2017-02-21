include:
  - base: repository
  - base: package

{% for packagename, package in pillar.get('web-service-packages', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest:
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
    - require:
      - sls: repository
      - sls: package
{% endfor %}

{% for packagename, package in pillar.get('web-service-python-packages', {}).items() %}
{{ packagename }}:
  pip.installed:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - name: {{ packagename }}
    - upgrade: True
{% elif 'version' in package %}
    - name: {{ packagename }} {{ package['version'] }}
{% endif %}
    - require:
      - sls: repository
      - sls: package
{% endfor %}

