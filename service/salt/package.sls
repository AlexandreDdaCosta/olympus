packages:
{% if pillar['initialization'] == True or pillar['pkg.latest'] == True %}
  pkg.installed:
    - pkgs:
    {% for packagename, package in pillar.get('core-packages', {}).items() %}
      {{ packagename }}:
    {% endfor %}
{% else %}
{% for packagename, package in pillar.get('core-packages', {}).items() %}
  {{ packagename }}:
    pkg.installed:
      - version: {{ package['version'] }}
{% endfor %}
{% endif %}
