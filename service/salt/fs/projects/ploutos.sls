{% set ploutos_user='ploutos' %}
{% set project_ploutos_path=pillar.projects_path+'/ploutos' %}

include:
  - base: projects
  - base: services.bigdata

{% for packagename, package in pillar.get('ploutos-pip3-packages', {}).items() %}
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

{{ ploutos_user }}:
  group:
    - name: {{ ploutos_user }}
    - present
  user:
    - createhome: True
    - fullname: {{ ploutos_user }}
    - home: /home/{{ ploutos_user }}
    - name: {{ ploutos_user }}
    - present
    - shell: /bin/false
    - groups:
      - {{ ploutos_user }}

/home/{{ ploutos_user }}/Downloads:
  file.directory:
    - group: {{ ploutos_user }}
    - makedirs: False
    - mode: 0755
    - user: {{ ploutos_user }}

{{ project_ploutos_path }}:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: {{ ploutos_user }}
    - source: salt://project/ploutos
    - require:
      - sls: projects
      - sls: services.bigdata
    - user: {{ ploutos_user }}
  cmd.run:
    - name: 'chmod -R 0755 {{ project_ploutos_path }}/scripts'

{{ pillar['olympus-package-path']  }}/projects/ploutos:
  file.recurse:
    - clean: True
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://projects/ploutos/files/lib
    - user: root

initialize_ploutos:
  cmd.run:
    - name: "su -s /bin/bash -c '/srv/projects/ploutos/scripts/init.py --graceful' {{ ploutos_user }}"
