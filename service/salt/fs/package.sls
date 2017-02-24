include:
  - repository

{% for packagename, package in pillar.get('packages', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if package is defined and 'version' in package %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
    - require:
      - sls: repository
{% endfor %}
