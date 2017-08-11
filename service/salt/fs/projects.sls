{{ pillar.projects_path }}:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root

/usr/lib/tmpfiles.d/olympus.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://projects/files/tmpfiles.d/olympus.conf
    - user: root

{{ pillar['olympus-package-path']  }}/projects:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0755
    - user: root
