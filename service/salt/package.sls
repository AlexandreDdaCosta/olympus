{% for packagename, package in pillar.get('core-packages', {}).items() %}
{{ packagename }}:
{% if pillar.initialization is defined and pillar.initialization or pillar.pkg_latest is defined %}
  pkg.latest
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
{% endfor %}
