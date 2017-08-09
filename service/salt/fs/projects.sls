{{ pillar.projects_path }}:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

/run/olympus/projects:
  file.directory:
    - group: root
    - makedirs: True
    - mode: 0755
    - user: root
