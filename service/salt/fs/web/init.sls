include:
  - base: repository

{% for packagename, package in pillar.get('web-service-packages', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest:
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
{% if package['fromrepo'] is defined %}
    - fromrepo: {{ package['fromrepo'] }}
{% endif %}
    - require:
      - sls: repository
{% endfor %}
