{% set ploutos_user='ploutos' %}
{% set project_ploutos_path=pillar.projects_path+'/ploutos' %}

include:
  - base: projects
  - base: services.bigdata

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

/run/olympus/projects/ploutos:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

/var/run/olympus/projects/ploutos/init.pid:
  file.managed:
    - group: {{ ploutos_user }}
    - mode: 0644
    - replace: False
    - user: {{ ploutos_user }}

{{ project_ploutos_path }}:
  file.recurse:
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

initialize_ploutos:
  cmd.run:
    - name: "su -s /bin/bash -c '/srv/projects/ploutos/scripts/init.py' {{ ploutos_user}}"
