/tmp/testsalt8:
  file.managed:
    - source: salt://conf/minion.d/zeus.conf
    - user: root
    - group: root
    - mode: 644
