{% if pillar['initialization'] == True or pillar['pkg.latest'] == True %}
{% for packagename, package in pillar.get('core-packages', {}).items() %}
{{ packagename }}:
  pkg.latest
{% endfor %}
{% else %}
{% for packagename, package in pillar.get('core-packages', {}).items() %}
{{ packagename }}:
  pkg.installed:
    - version: {{ package['version'] }}
{% endfor %}
{% endif %}
