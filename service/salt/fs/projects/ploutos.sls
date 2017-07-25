{% set project_ploutos_path=pillar.projects_path+'/ploutos' %}

include:
  - base: projects
  - base: services.bigdata

{{ project_ploutos_path }}:
  file.recurse:
    - dir_mode: 0755
    - file_mode: 0644
    - group: root
    - source: salt://project/ploutos
    - require:
      - sls: projects
      - sls: services.bigdata
    - user: root
