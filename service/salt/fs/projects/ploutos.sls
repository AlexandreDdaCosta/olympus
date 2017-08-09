{% set ploutos_user='ploutos' %}
{% set project_ploutos_path=pillar.projects_path+'/ploutos' %}

include:
  - base: projects
  - base: services.bigdata

ploutos-user:
  user.present:
    - createhome: True
    - fullname: {{ ploutos_user }}
    - name: {{ ploutos_user }}
    - shell: /bin/false
    - home: /home/{{ ploutos_user }}
    - groups:
      - {{ ploutos_user }}

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
    - name: 'su - {{ ploutos_user}} {{ project_ploutos_path }}/scripts/init.py'
