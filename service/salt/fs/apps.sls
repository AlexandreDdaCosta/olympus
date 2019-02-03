{% for packagename, package in pillar.get('widgets-pip3-packages', {}).items() %}
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
{% endfor %}

{{ pillar.apps_path }}:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - require:
      - sls: services.bigdata
    - user: root

/usr/lib/tmpfiles.d/olympus.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://apps/files/tmpfiles.d/olympus.conf
    - user: root

{{ pillar['olympus-package-path']  }}/apps:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root
