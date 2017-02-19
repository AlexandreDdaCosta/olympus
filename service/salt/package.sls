{% for packagename, package in pillar.get('core-packages', {}).items() %}
{{ packagename }}:
{% if pillar.initialization or pillar.pkg.latest %}
  pkg.latest
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
{% endfor %}
