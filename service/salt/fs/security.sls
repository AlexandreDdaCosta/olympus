/etc/ssl/localcerts:
  file.directory:
    - group: root
    - makedirs: False
    - mode: 0600
    - user: root
