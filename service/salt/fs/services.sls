atd:
  service.running:
    - enable: True
    - watch:
        - pkg: at
ntpdate:
  service.running:
    - enable: True
      
ntpd:
  service.running:
    - enable: True
    - watch:
        - pkg: ntp

ntpd-timecheck:
  cmd.run:
    - name: service ntpd stop; ntpdate pool.ntp.org; service ntpd start
