{% for packagename, package in pillar.get('core-packages', {}).items() %}
{{ packagename }}:
  pkg.installed:
    - version: {{ package['version'] }}
{% endfor %}
