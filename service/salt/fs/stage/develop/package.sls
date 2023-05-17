include:
  - repository
  - package

{% for packagename, package in pillar.get('develop-packages', {}).items() %}
{{ packagename }}:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if package and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
    {% endif %}
{% endif %}
{% if package != None and 'repo' in package %}
    - fromrepo: {{ package['repo'] }}
{% endif %}
    - require:
      - sls: repository
{% endfor %}

{% for packagename, package in pillar.get('develop-pip3-packages', {}).items() %}
{{ packagename }}:
  pip.installed:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
    - name: {{ packagename }}
    - upgrade: True
{% elif package != None and 'version' in package %}
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - name: {{ packagename }} {{ package['version'] }}
    {% else %}
    - name: {{ packagename }}
    {% endif %}
{% else %}
    - name: {{ packagename }}
{% endif %}
    - bin_env: '/usr/bin/pip3'
    - require:
      - sls: repository
{% endfor %}

{% for packagename in pillar['develop-pip3-packages'] %}
{{ packagename }}:
  - cpan.install
