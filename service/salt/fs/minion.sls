salt-minion:
{% if pillar.pkg_latest is defined and pillar.pkg_latest %}
  pkg.latest
{% else %}
  pkg.installed:
    - version: 3004.1+ds-1
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
        - pkg: salt-minion
