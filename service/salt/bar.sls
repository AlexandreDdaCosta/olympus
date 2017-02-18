/tmp/testsalt3:
  file.managed:
    - user: root
    - group: root
    - mode: 644

/tmp/testsalt4:
  file.managed:
    - source: salt://service/salt/conf/minion.d/zeus.conf
    - user: root
    - group: root
    - mode: 644

/tmp/testsalt5:
  file.managed:
    - source: salt://conf/minion.d/zeus.conf
    - user: root
    - group: root
    - mode: 644
