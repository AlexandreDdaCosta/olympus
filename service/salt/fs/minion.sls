{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
Disable starting services:
  file.managed:
    - name: /usr/sbin/policy-rc.d
    - user: root
    - group: root
    - mode: 0755
    - contents:
      - '#!/bin/sh'
      - exit 101
    # do not touch if already exists
    - replace: False
    - prereq:
      - pkg: salt-minion

salt-minion:
  pkg.latest

Enable starting services:
  file.absent:
    - name: /usr/sbin/policy-rc.d
    - onchanges:
      - pkg: salt-minion
{% endif %}

/etc/salt/minion.d/core.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/minion.d/core.conf
    - user: root

{% set server_conf_file=grains.get('server') %}
/etc/salt/minion.d/{{ server_conf_file }}.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/minion.d/{{ server_conf_file }}.conf
    - user: root

salt-minion-service-restart:
  cmd.run:
    - bg: True
    - name: 'salt-call service.restart salt-minion'
    - onchanges:
        - file: /etc/salt/minion.d/core.conf
        - file: /etc/salt/minion.d/{{ server_conf_file  }}.conf
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
        - pkg: salt-minion
{% endif %}
