{% set project_ploutos_path=pillar.projects_path+'/ploutos' %}

include:
  - base: projects
  - base: services.bigdata

{{ project_ploutos_path }}:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root
    - require:
      - sls: projects
      - sls: services.bigdata
