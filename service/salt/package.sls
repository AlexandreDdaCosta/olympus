{% for packagename, package in pillar.get('core-packages', {}).items() %}
{{ packagename }}:
{% if initialization in pillar or pillar.pkg.latest %}
  pkg.latest
{% else %}
  pkg.installed:
    - version: {{ package['version'] }}
{% endif %}
{% endfor %}
