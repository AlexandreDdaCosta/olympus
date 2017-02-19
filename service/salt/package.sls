include:
  - repository

{% for packagename, package in pillar.get('packages', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
{% endfor %}
