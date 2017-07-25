{{ pillar.projects_path }}:
    file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root
