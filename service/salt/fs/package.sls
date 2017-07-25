include:
  - repository

{% for packagename, package in pillar.get('packages', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if package and 'version' in package %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
{% if package != None and 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: repository
{% endfor %}
