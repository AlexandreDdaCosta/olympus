{%- if grains.get('server') == 'supervisor' or grains.get('server') == 'unified' %}

salt-master:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest
{% else %}
  pkg.installed:
    - version: 3004.1+ds-1
{% endif %}

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
