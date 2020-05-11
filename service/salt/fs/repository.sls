include:
  - base: grains

/etc/apt/sources.list:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://repository/sources.list.jinja
    - template: jinja
    - user: root

{% for packagename, package in pillar.get('repo-packages', {}).items() %}
{{ packagename }}-repo:
{% if pillar.pkg_latest is defined and pillar.pkg_latest or 'version' not in package %}
  pkg.latest:
{% else %}
  pkg.installed:
    {% if pillar.pkg_noversion is not defined or not pillar.pkg_noversion %}
    - version: {{ package['version'] }}
    {% endif %}
{% endif %}
    - name: {{ packagename }}
{% endfor %}

delete_old_backports_file:
  file.absent:
    - name: /etc/apt/sources.list.d/{{ pillar['previous-release'] }}-backports.list:

