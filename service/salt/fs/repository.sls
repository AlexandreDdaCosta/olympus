include:
  - base: grains

/etc/apt/sources.list:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://repository/sources.list.jinja
    - template: jinja
    - user: root

