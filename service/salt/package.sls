{% for packagename, package in pillar.get('core-packages', {}).items() %}
{{ packagename }}:
{% if pillar.initializationed or pillar.pkg.latest %}
  pkg.latest
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
{% endfor %}
