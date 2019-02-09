{%- if grains.get('server') %}
{%- if grains.get('server') == 'supervisor' or grains.get('server') == 'unified' %}

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
      - pkg: salt-master

salt-master:
  pkg.latest

Enable starting services:
  file.absent:
    - name: /usr/sbin/policy-rc.d
    - onchanges:
      - pkg: salt-master

/etc/salt/master.d/core.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/master.d/core.conf
    - user: root

/etc/salt/master.d/reactor.conf:
  file.managed:
    - group: root
    - makedirs: False
    - mode: 0644
    - source: salt://saltstack/files/master.d/reactor.conf
    - user: root

salt-master-service-restart:
  cmd.run:
    - bg: True
    - name: 'salt-call service.restart salt-master'
    - onchanges:
        - file: /etc/salt/master.d/core.conf
        - file: /etc/salt/master.d/reactor.conf
        - pkg: salt-master

{% endif %}
{% endif %}
