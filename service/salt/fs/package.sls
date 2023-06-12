include:
  - repository

{% for packagename, package in pillar.get('packages', {}).items() %}
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

{% for packagename, package in pillar.get('firmware', {}).items() %}
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
    - require:
      - sls: repository
{% endfor %}

{% for packagename, package in pillar.get('pip3-packages', {}).items() %}
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

/etc/sysfs.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://package/files/sysfs.conf
    - user: root

{# Another temporary bug fix, this time for mismatch of salt and py docker versions #}
salt-3005-docker-bug:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - name: /usr/lib/python3/dist-packages/salt/modules/dockermod.py
    - source: salt://saltstack/files/dockermod.py
    - user: root

{{ pillar['olympus-package-path'] }}:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://core/lib
    - user: root
  cmd.run:
    - name: "find {{ pillar['olympus-package-path'] }} -type f | grep -E 'test/.*?\\.py$' | xargs -r chmod 0755"

{{ pillar['olympus-scripts-path'] }}:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0755
    - group: root
    - source: salt://core/bin
    - user: root
